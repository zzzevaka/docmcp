"""MCP (Model Context Protocol) routes for exposing project documents to LLM agents."""

import json
import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.projects.models import Document, DocumentType
from app.projects.repositories import DocumentRepository, ProjectRepository
from app.users.api.dependencies import verify_project_access
from app.users.models import User

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "docs-mcp-server", "version": "1.0.0"}


# Image handling for markdown documents
# Pattern supports both formats:
# - ![caption](data:image/png;base64,...)
# - ![caption](data:image/png;base64,... "title")
# Groups: 1=caption, 2=mime_type, 3=base64_data, 4=title (optional)
IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(data:image/([^;]+);base64,([^"\s)]+)(?:\s+"([^"]*)")?\)')


def extract_images_from_markdown(markdown: str) -> tuple[str, list[dict[str, str]]]:
    """
    Extract base64 images from markdown and replace with placeholders.

    Args:
        markdown: Markdown content with embedded base64 images

    Returns:
        Tuple of (modified_markdown, list_of_images)
        - modified_markdown: Markdown with images replaced by [image:N] placeholders
        - list_of_images: List of dicts with keys: alt, mime_type, data
    """
    images: list[dict[str, str]] = []

    def replace_image(match: re.Match) -> str:
        caption = match.group(1)
        mime_type = match.group(2)
        base64_data = match.group(3)
        title = match.group(4) if match.lastindex >= 4 else None

        image_index = len(images)
        image_data = {
            "caption": caption,
            "mime_type": mime_type,
            "data": base64_data,
        }
        if title:
            image_data["title"] = title

        images.append(image_data)

        return f"[image:{image_index}]"

    modified_markdown = IMAGE_PATTERN.sub(replace_image, markdown)
    return modified_markdown, images


def restore_images_to_markdown(markdown: str, images: list[dict[str, str]]) -> str:
    """
    Restore base64 images from placeholders back into markdown.

    Args:
        markdown: Markdown content with [image:N] placeholders
        images: List of dicts with keys: caption, mime_type, data, title (optional)
               Also supports legacy format with 'alt' key for backward compatibility

    Returns:
        Markdown with placeholders replaced by actual base64 images
    """
    def replace_placeholder(match: re.Match) -> str:
        image_index = int(match.group(1))
        if 0 <= image_index < len(images):
            img = images[image_index]
            # Support both new format (caption/title) and legacy format (alt)
            caption = img.get("caption", img.get("alt", ""))
            mime_type = img["mime_type"]
            data = img["data"]
            title = img.get("title")

            # Build markdown image syntax
            if title:
                return f'![{caption}](data:image/{mime_type};base64,{data} "{title}")'
            else:
                return f"![{caption}](data:image/{mime_type};base64,{data})"
        # If image not found, keep placeholder
        return match.group(0)

    placeholder_pattern = re.compile(r"\[image:(\d+)\]")
    return placeholder_pattern.sub(replace_placeholder, markdown)


TOOLS = [
    {
        "name": "list_documents",
        "description": (
            "Returns list of all project documents with their hierarchical structure "
            "(id, name, editable_by_agent, descendants)"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "search_documents",
        "description": (
            "Search for documents by name or content. "
            "Returns matching documents with their IDs, names, and types."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to match against document names and content",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_document",
        "description": (
            "Returns full content of a specific document by ID along with all its parent documents. "
            "Documents are returned in hierarchical order from root to the requested document, separated by '---'. "
            "For markdown documents with embedded base64 images: images are extracted and replaced "
            "with placeholders like [image:0], [image:1], etc. The images are provided separately "
            "as image content blocks. When editing such documents, use these placeholders to preserve images."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "ID of the document",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "edit_document",
        "description": (
            "Edit an existing document's content. "
            "Only documents with editable_by_agent=true can be edited. "
            "For markdown documents with images: use placeholders like [image:0], [image:1] in your content "
            "to preserve images from the original document. The placeholders will be automatically replaced "
            "with the actual base64 images during save."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "ID of the document to edit",
                },
                "content": {
                    "type": "string",
                    "description": (
                        "New content for the document. For markdown with images, use [image:N] placeholders "
                        "to reference images from get_document response. Content will be stored based on document type."
                    ),
                },
            },
            "required": ["document_id", "content"],
        },
    },
    {
        "name": "create_document",
        "description": "Create a new document in the project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title/name of the document",
                },
                "type": {
                    "type": "string",
                    "description": "Document type (markdown or whiteboard)",
                    "enum": ["markdown", "whiteboard"],
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Content of the document. "
                        "Content of markdown documents should be plain markdown. "
                        "Content of whiteboards should be JSON in Excalidraw format."
                    ),
                },
            },
            "required": ["title", "type", "content"],
        },
    },
]


def build_document_tree(document: Document, all_docs: list[Document]) -> dict[str, Any]:
    """Build a document tree structure with descendants."""
    children = [doc for doc in all_docs if doc.parent_id == document.id]

    result = {
        "id": str(document.id),
        "name": document.name,
        "editable_by_agent": document.editable_by_agent,
    }

    if children:
        result["descendants"] = [build_document_tree(child, all_docs) for child in children]

    return result


async def list_documents_tool(project_id: UUID, db: AsyncSession) -> dict[str, Any]:
    """List all documents with hierarchical structure."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists (auth is handled by endpoint dependency)
    project = await project_repo.get(project_id)
    if not project:
        raise ValueError("Project not found")

    # Get all documents
    documents = await document_repo.list_for_project(project_id)
    all_docs = list(documents)

    # Build tree structure starting from root documents (no parent)
    root_documents = [doc for doc in all_docs if doc.parent_id is None]
    document_trees = [build_document_tree(doc, all_docs) for doc in root_documents]

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"documents": document_trees}, indent=2, ensure_ascii=False),
            }
        ]
    }


async def search_documents_tool(project_id: UUID, query: str, db: AsyncSession) -> dict[str, Any]:
    """Search for documents by name or content using SQL full-text search."""

    project_repo = ProjectRepository(db)

    # Check if project exists
    project = await project_repo.get(project_id)
    if not project:
        raise ValueError("Project not found")

    # Split query into words and search for each word
    words = query.strip().split()
    search_conditions = []

    for word in words:
        if word:  # Skip empty strings
            word_pattern = f"%{word}%"
            search_conditions.append(
                or_(
                    func.lower(Document.name).ilike(func.lower(word_pattern)),
                    func.lower(Document.content).ilike(func.lower(word_pattern)),
                )
            )

    # Combine all conditions with OR (documents matching any word)
    if search_conditions:
        combined_condition = or_(*search_conditions)
    else:
        # If no valid words, use original query
        search_pattern = f"%{query}%"
        combined_condition = or_(
            func.lower(Document.name).ilike(func.lower(search_pattern)),
            func.lower(Document.content).ilike(func.lower(search_pattern)),
        )

    result = await db.execute(
        select(Document)
        .where(
            Document.project_id == project_id,
            combined_condition,
        )
        .order_by(Document.created_at.asc())
    )
    matching_docs = result.scalars().all()

    results = [
        {
            "id": str(doc.id),
            "name": doc.name,
            "type": doc.type.value,
        }
        for doc in matching_docs
    ]

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {"query": query, "results": results},
                    indent=2,
                    ensure_ascii=False,
                ),
            }
        ]
    }


async def get_document_tool(project_id: UUID, document_id: str, db: AsyncSession) -> dict[str, Any]:
    """Get the full content of a specific document along with all its parent documents."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists
    project = await project_repo.get(project_id)
    if not project:
        raise ValueError("Project not found")

    # Parse document ID
    try:
        doc_uuid = UUID(document_id)
    except ValueError as e:
        raise ValueError("Invalid document ID format") from e

    document = await document_repo.get(doc_uuid)
    if not document or document.project_id != project_id:
        raise ValueError("Document not found")

    # Collect all parent documents (from root to requested document)
    documents_chain = [document]
    current_doc = document

    while current_doc.parent_id is not None:
        parent = await document_repo.get(current_doc.parent_id)
        if parent is None:
            break
        documents_chain.insert(0, parent)  # Insert at beginning to have parents first
        current_doc = parent

    # Build content blocks for all documents in the chain
    content_blocks = []

    for doc in documents_chain:
        try:
            if isinstance(doc.content, str):
                content = json.loads(doc.content)
            else:
                content = doc.content
        except json.JSONDecodeError:
            content = doc.content

        # Add document title
        content_blocks.append(
            {
                "type": "text",
                "text": f"Title: {doc.name}",
            }
        )

        # Add document type-specific content
        if doc.type.value == "markdown":
            # For markdown documents, extract images and replace with placeholders
            markdown_text = ""
            if isinstance(content, dict) and "markdown" in content:
                markdown_text = content["markdown"]
            elif isinstance(content, dict) and "text" in content:
                markdown_text = content["text"]
            else:
                markdown_text = json.dumps(content, indent=2)

            # Extract images from markdown
            modified_markdown, images = extract_images_from_markdown(markdown_text)

            # Save images to document content for future restoration
            if images:
                if isinstance(content, dict):
                    content["images"] = images
                else:
                    content = {"markdown": markdown_text, "images": images}
                doc.content = json.dumps(content)
                await db.commit()
                await db.refresh(doc)

            # Add modified markdown as text
            content_blocks.append(
                {
                    "type": "text",
                    "text": modified_markdown,
                }
            )

            # Add each image separately
            for img in images:
                content_blocks.append(
                    {
                        "type": "image",
                        "data": img["data"],
                        "mimeType": f"image/{img['mime_type']}",
                    }
                )
        elif doc.type.value == "whiteboard":
            # For whiteboard documents, return base64 image if available
            if isinstance(content, dict) and "image" in content:
                content_image = content["image"].split(",")[-1]
                content_blocks.append({"type": "image", "data": content_image, "mimeType": "image/png"})
            # Add raw content as text
            if isinstance(content, dict) and "raw" in content:
                content_blocks.append(
                    {
                        "type": "text",
                        "text": json.dumps(content["raw"], indent=2),
                    }
                )
            else:
                # Fallback: show full content if no 'raw' field
                content_blocks.append(
                    {
                        "type": "text",
                        "text": f"Excalidraw whiteboard content:\n{json.dumps(content, indent=2)}",
                    }
                )

        # Add separator between documents (except after the last one)
        if doc != documents_chain[-1]:
            content_blocks.append(
                {
                    "type": "text",
                    "text": "\n---\n",
                }
            )

    return {"content": content_blocks}


async def edit_document_tool(
    project_id: UUID, document_id: str, content: str, db: AsyncSession
) -> dict[str, Any]:
    """Edit an existing document's content."""
    project_repo = ProjectRepository(db)
    document_repo = DocumentRepository(db)

    # Check if project exists
    project = await project_repo.get(project_id)
    if not project:
        raise ValueError("Project not found")

    # Parse document ID
    try:
        doc_uuid = UUID(document_id)
    except ValueError as e:
        raise ValueError("Invalid document ID format") from e

    # Get document
    document = await document_repo.get(doc_uuid)
    if not document or document.project_id != project_id:
        raise ValueError("Document not found")

    # Check if document is editable by agent
    if not document.editable_by_agent:
        raise ValueError("This document is not editable by agents. Set editable_by_agent=true first.")

    if document.type == DocumentType.MARKDOWN:
        # Get current content to extract saved images
        try:
            if isinstance(document.content, str):
                current_content = json.loads(document.content)
            else:
                current_content = document.content
        except json.JSONDecodeError:
            current_content = {}

        # Extract images from current content if they exist
        images = current_content.get("images", []) if isinstance(current_content, dict) else []

        # Restore images to markdown from placeholders
        restored_markdown = restore_images_to_markdown(content, images)

        # Save markdown with images preserved
        new_content = {"markdown": restored_markdown}
        # if images:
        #     new_content["images"] = images
    elif document.type == DocumentType.WHITEBOARD:
        try:
            new_content = {"raw": json.loads(content)}
        except json.JSONDecodeError as e:
            raise ValueError("Whiteboard content must be valid JSON") from e
    else:
        # Default: store as-is
        new_content = {"text": content}

    document.content = json.dumps(new_content)
    await db.commit()
    await db.refresh(document)

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "success": True,
                        "document_id": str(document.id),
                        "message": "Document updated successfully",
                    },
                    indent=2,
                ),
            }
        ]
    }


async def create_document_tool(
    project_id: UUID, title: str, doc_type: str, content: str, db: AsyncSession
) -> dict[str, Any]:
    """Create a new document in the project."""
    project_repo = ProjectRepository(db)

    project = await project_repo.get(project_id)
    if not project:
        raise ValueError("Project not found")

    try:
        document_type = DocumentType(doc_type)
    except ValueError as e:
        raise ValueError("Invalid document type. Must be 'markdown' or 'whiteboard'") from e

    if document_type == DocumentType.MARKDOWN:
        doc_content = {"markdown": content}
    elif document_type == DocumentType.WHITEBOARD:
        try:
            doc_content = {
                "raw": json.loads(content),
            }
        except json.JSONDecodeError as e:
            raise ValueError("Whiteboard content must be valid JSON") from e
    else:
        doc_content = {"text": content}

    new_document = Document(
        name=title,
        project_id=project_id,
        type=document_type,
        content=json.dumps(doc_content),
        editable_by_agent=True,
    )

    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "success": True,
                        "document_id": str(new_document.id),
                        "message": "Document created successfully",
                    },
                    indent=2,
                ),
            }
        ]
    }


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], project_id: UUID, db: AsyncSession
) -> dict[str, Any]:
    """Execute a tool by name."""
    if tool_name == "list_documents":
        return await list_documents_tool(project_id, db)
    elif tool_name == "search_documents":
        query = arguments.get("query", "")
        return await search_documents_tool(project_id, query, db)
    elif tool_name == "get_document":
        document_id = arguments.get("id", "")
        return await get_document_tool(project_id, document_id, db)
    elif tool_name == "edit_document":
        document_id = arguments.get("document_id", "")
        content = arguments.get("content", "")
        return await edit_document_tool(project_id, document_id, content, db)
    elif tool_name == "create_document":
        title = arguments.get("title", "")
        doc_type = arguments.get("type", "")
        content = arguments.get("content", "")
        return await create_document_tool(project_id, title, doc_type, content, db)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


async def handle_mcp_request(
    request_data: dict[str, Any], project_id: UUID, db: AsyncSession
) -> dict[str, Any]:
    """Handle MCP JSON-RPC request."""
    method = request_data.get("method")
    params = request_data.get("params", {})

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        }

    elif method == "tools/list":
        return {"tools": TOOLS}

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        return await execute_tool(tool_name, arguments, project_id, db)

    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")


@router.post("/{project_id}")
async def mcp_endpoint(
    request: Request,
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(verify_project_access),
):
    """
    Main MCP communication endpoint.
    Supports both regular JSON responses and Server-Sent Events (SSE).
    Requires Bearer token authentication.
    """
    try:
        body = await request.body()
        request_data = json.loads(body)

        response_data = await handle_mcp_request(request_data, project_id, db)

        # Format response in JSON-RPC 2.0 format
        result = {"jsonrpc": "2.0", "id": request_data.get("id"), "result": response_data}

        # Check if streaming response is needed
        accept_header = request.headers.get("accept", "")

        if "text/event-stream" in accept_header:
            # Return SSE for streaming
            async def event_generator():
                yield f"data: {json.dumps(result)}\n\n"

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )
        else:
            # Regular JSON response
            return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON") from e
    except Exception as e:
        # Format error in JSON-RPC 2.0 format
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if "request_data" in locals() else None,
            "error": {"code": -32603, "message": str(e)},
        }
