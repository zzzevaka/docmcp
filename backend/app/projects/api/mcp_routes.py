"""MCP (Model Context Protocol) routes for exposing project documents to LLM agents."""

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.projects.models import Document, DocumentType
from app.projects.repositories import DocumentRepository, ProjectRepository

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "docs-mcp-server", "version": "1.0.0"}


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
        "description": "Returns full content of a specific document by ID",
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
            "Only documents with editable_by_agent=true can be edited."
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
                    "description": "New content for the document (will be stored based on document type)",
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

    # Check if project exists (no auth required for MCP)
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

    # Use SQL ILIKE for case-insensitive full-text search
    search_pattern = f"%{query}%"

    result = await db.execute(
        select(Document)
        .where(
            Document.project_id == project_id,
            or_(
                func.lower(Document.name).ilike(func.lower(search_pattern)),
                func.lower(Document.content).ilike(func.lower(search_pattern)),
            ),
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
    """Get the full content of a specific document."""
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

    try:
        if isinstance(document.content, str):
            content = json.loads(document.content)
        else:
            content = document.content
    except json.JSONDecodeError:
        content = document.content

    content_blocks = [
        {
            "type": "text",
            "text": f"Title: {document.name}",
        }
    ]

    # Add document type-specific content
    if document.type.value == "markdown":
        # For markdown documents, add the markdown text
        if isinstance(content, dict) and "markdown" in content:
            content_blocks.append(
                {
                    "type": "text",
                    "text": content["markdown"],
                }
            )
        elif isinstance(content, dict) and "text" in content:
            content_blocks.append(
                {
                    "type": "text",
                    "text": content["text"],
                }
            )
        else:
            content_blocks.append(
                {
                    "type": "text",
                    "text": json.dumps(content, indent=2),
                }
            )
    elif document.type.value == "whiteboard":
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
        new_content = {"markdown": content}
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
async def mcp_endpoint(request: Request, project_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Main MCP communication endpoint.
    Supports both regular JSON responses and Server-Sent Events (SSE).
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
