"""Tests for MCP routes."""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.main import app
from app.projects.api.mcp_routes import extract_images_from_markdown, restore_images_to_markdown
from app.projects.models import Document, DocumentType, Project
from app.users.models import ApiToken, Team, TeamMember, TeamRole, User


def get_auth_headers(token: str) -> dict[str, str]:
    """Helper to get authentication headers."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client_with_db(db_session: AsyncSession):
    """Create test client with database session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_project(db_session: AsyncSession):
    """Create a test project with documents and API token."""
    # Create user and team
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.flush()

    # Create project
    project = Project(name="Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    # Create documents with hierarchy
    root_doc1 = Document(
        name="Getting Started",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content=json.dumps({"text": "Welcome to the project"}),
        parent_id=None,
        order=0,
    )
    db_session.add(root_doc1)
    await db_session.flush()

    child_doc1 = Document(
        name="Installation",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content=json.dumps({"text": "How to install"}),
        parent_id=root_doc1.id,
        order=0,
    )
    db_session.add(child_doc1)
    await db_session.flush()

    child_doc2 = Document(
        name="Configuration",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content=json.dumps({"text": "How to configure"}),
        parent_id=root_doc1.id,
        order=1,
    )
    db_session.add(child_doc2)
    await db_session.flush()

    root_doc2 = Document(
        name="Architecture",
        project_id=project.id,
        type=DocumentType.WHITEBOARD,
        content=json.dumps(
            {
                "elements": [],
                "appState": {},
                "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",  # 1x1 transparent PNG
            }
        ),
        parent_id=None,
        order=1,
    )
    db_session.add(root_doc2)
    await db_session.flush()

    # Create API token for authentication
    api_token = ApiToken(
        name="Test Token",
        user_id=user.id,
        token="test_token_123456"
    )
    db_session.add(api_token)

    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(root_doc1)
    await db_session.refresh(child_doc1)
    await db_session.refresh(child_doc2)
    await db_session.refresh(root_doc2)
    await db_session.refresh(user)
    await db_session.refresh(api_token)

    return {
        "project": project,
        "user": user,
        "team": team,
        "api_token": api_token,
        "root_doc1": root_doc1,
        "child_doc1": child_doc1,
        "child_doc2": child_doc2,
        "root_doc2": root_doc2,
    }


@pytest.mark.asyncio
async def test_initialize(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test MCP initialize method."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 1
    assert "result" in data
    assert data["result"]["protocolVersion"] == "2024-11-05"
    assert "serverInfo" in data["result"]
    assert "capabilities" in data["result"]


@pytest.mark.asyncio
async def test_tools_list(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test MCP tools/list method."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    assert "tools" in data["result"]
    assert len(data["result"]["tools"]) == 5

    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    assert "list_documents" in tool_names
    assert "search_documents" in tool_names
    assert "get_document" in tool_names
    assert "edit_document" in tool_names
    assert "create_document" in tool_names


@pytest.mark.asyncio
async def test_list_documents_tool(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test list_documents tool."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "list_documents", "arguments": {}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 3
    assert "result" in data
    assert "content" in data["result"]
    assert len(data["result"]["content"]) == 1
    assert data["result"]["content"][0]["type"] == "text"

    # Parse the text content
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert "documents" in text_data
    assert len(text_data["documents"]) == 2  # Two root documents

    # Check first root document
    doc1 = next(d for d in text_data["documents"] if d["name"] == "Getting Started")
    assert "id" in doc1
    assert "editable_by_agent" in doc1
    assert "descendants" in doc1
    assert len(doc1["descendants"]) == 2


@pytest.mark.asyncio
async def test_search_documents_tool(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test search_documents tool."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "search_documents", "arguments": {"query": "installation"}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert "content" in data["result"]

    # Parse the text content
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["query"] == "installation"
    assert len(text_data["results"]) == 1
    assert text_data["results"][0]["name"] == "Installation"
    assert text_data["results"][0]["type"] == "markdown"


@pytest.mark.asyncio
async def test_search_documents_multiple_words(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test search_documents tool with multiple words - should find documents containing any word."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "tools/call",
        "params": {"name": "search_documents", "arguments": {"query": "installation configure"}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert "content" in data["result"]

    # Parse the text content
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["query"] == "installation configure"

    # Should find both "Installation" and "Configuration" documents
    # because query is split into ["installation", "configure"] and each word is searched separately
    assert len(text_data["results"]) == 2

    result_names = [r["name"] for r in text_data["results"]]
    assert "Installation" in result_names
    assert "Configuration" in result_names


@pytest.mark.asyncio
async def test_get_document_tool(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test get_document tool."""
    project = test_project["project"]
    token = test_project["api_token"].token
    doc = test_project["root_doc1"]

    request_data = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(doc.id)}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert "content" in data["result"]

    # Check content blocks
    content_blocks = data["result"]["content"]
    assert len(content_blocks) >= 1
    assert content_blocks[0]["type"] == "text"
    assert "Getting Started" in content_blocks[0]["text"]


@pytest.mark.asyncio
async def test_get_document_with_parents(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test get_document tool returns document with all parent documents."""
    project = test_project["project"]
    token = test_project["api_token"].token
    child_doc = test_project["child_doc1"]  # Installation (child of Getting Started)

    request_data = {
        "jsonrpc": "2.0",
        "id": 22,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(child_doc.id)}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert "content" in data["result"]

    # Check content blocks - should contain parent document first, then child
    content_blocks = data["result"]["content"]

    # Convert to text for easier checking
    full_text = "\n".join([block.get("text", "") for block in content_blocks if block["type"] == "text"])

    # Should contain both parent and child document titles
    assert "Getting Started" in full_text
    assert "Installation" in full_text

    # Should contain separator between documents
    assert "---" in full_text

    # Parent should appear before child (check order)
    getting_started_pos = full_text.find("Getting Started")
    installation_pos = full_text.find("Installation")
    assert getting_started_pos < installation_pos, "Parent document should appear before child"


@pytest.mark.asyncio
async def test_get_document_whiteboard(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test get_document with whiteboard document returns base64 image."""
    project = test_project["project"]
    token = test_project["api_token"].token
    doc = test_project["root_doc2"]

    request_data = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(doc.id)}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    content_blocks = data["result"]["content"]
    assert len(content_blocks) >= 2

    # First block should be the title
    assert "Architecture" in content_blocks[0]["text"]

    # Second block should be the image
    assert content_blocks[1]["type"] == "image"
    assert "data" in content_blocks[1]
    assert content_blocks[1]["mimeType"] == "image/png"
    assert content_blocks[1]["data"].startswith("iVBORw0KGgo")  # PNG header in base64


@pytest.mark.asyncio
async def test_unknown_method(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test unknown method returns error."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {"jsonrpc": "2.0", "id": 7, "method": "unknown_method", "params": {}}

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    # Unknown method should return HTTP 400 or JSON-RPC error
    if response.status_code == 200:
        data = response.json()
        assert "error" in data
    else:
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_invalid_json(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test invalid JSON returns error."""
    project = test_project["project"]
    token = test_project["api_token"].token

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        content=b"invalid json",
        headers=get_auth_headers(token)
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_nonexistent_project(
    client_with_db: AsyncClient,
    test_project: dict,
) -> None:
    """Test with nonexistent project."""
    token = test_project["api_token"].token
    fake_uuid = uuid4()
    request_data = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {"name": "list_documents", "arguments": {}},
    }

    response = await client_with_db.post(f"/api/mcp/{fake_uuid}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 404  # Should be 404 since project not found
    assert "Project not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_empty_project(client_with_db: AsyncClient, db_session: AsyncSession) -> None:
    """Test list_documents with project that has no documents."""
    # Create user and team
    user = User(username="emptyuser", email="empty@example.com")
    db_session.add(user)
    team = Team(name="Empty Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)

    project = Project(name="Empty Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    # Create API token
    api_token = ApiToken(name="Empty Test Token", user_id=user.id, token="empty_token_123")
    db_session.add(api_token)
    await db_session.commit()

    request_data = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {"name": "list_documents", "arguments": {}},
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers("empty_token_123")
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["documents"] == []


@pytest.mark.asyncio
async def test_whiteboard_without_image(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """Test get_document with whiteboard document that has no image field."""
    # Create user and team
    user = User(username="wbuser", email="wb@example.com")
    db_session.add(user)
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)

    project = Project(name="Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Whiteboard No Image",
        project_id=project.id,
        type=DocumentType.WHITEBOARD,
        content=json.dumps({"elements": [], "appState": {}}),  # No image field
        parent_id=None,
        order=0,
    )
    db_session.add(doc)
    await db_session.flush()

    # Create API token
    api_token = ApiToken(name="WB Test Token", user_id=user.id, token="wb_token_123")
    db_session.add(api_token)
    await db_session.commit()
    await db_session.refresh(doc)

    request_data = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(doc.id)}},
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers("wb_token_123")
    )

    assert response.status_code == 200
    data = response.json()

    content_blocks = data["result"]["content"]
    assert len(content_blocks) >= 2

    # First block should be the title
    assert "Whiteboard No Image" in content_blocks[0]["text"]

    # Second block should be text (fallback) since no image
    assert content_blocks[1]["type"] == "text"
    assert "Excalidraw whiteboard content" in content_blocks[1]["text"]


@pytest.mark.asyncio
async def test_unknown_tool(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test calling unknown tool."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {"name": "unknown_tool", "arguments": {}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Unknown tool" in data["error"]["message"]


@pytest.mark.asyncio
async def test_get_document_invalid_id(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test get_document with invalid document ID format."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": "not-a-valid-uuid"}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Invalid document ID format" in data["error"]["message"]


@pytest.mark.asyncio
async def test_get_nonexistent_document(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test get_document with valid UUID but non-existent document."""
    project = test_project["project"]
    token = test_project["api_token"].token
    fake_doc_id = uuid4()

    request_data = {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(fake_doc_id)}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Document not found" in data["error"]["message"]


@pytest.mark.asyncio
async def test_search_no_results(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test search_documents with query that matches nothing."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {"name": "search_documents", "arguments": {"query": "xyzabc123nonexistent"}},
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["query"] == "xyzabc123nonexistent"
    assert text_data["results"] == []


@pytest.mark.asyncio
async def test_sse_support(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test SSE (Server-Sent Events) support."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {"jsonrpc": "2.0", "id": 15, "method": "initialize", "params": {}}

    # Send request with SSE Accept header
    headers = get_auth_headers(token)
    headers["Accept"] = "text/event-stream"
    response = await client_with_db.post(
        f"/api/mcp/{project.id}", json=request_data, headers=headers
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Check SSE format
    content = response.text
    assert content.startswith("data: ")
    assert content.endswith("\n\n")


@pytest.mark.asyncio
async def test_edit_document_tool(
    client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession
) -> None:
    """Test edit_document tool with editable document."""
    project = test_project["project"]
    token = test_project["api_token"].token
    doc = test_project["root_doc1"]

    # First, enable editable_by_agent
    doc.editable_by_agent = True
    await db_session.commit()
    await db_session.refresh(doc)

    new_content = "# Updated Content\n\nThis is the updated content."
    request_data = {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "tools/call",
        "params": {
            "name": "edit_document",
            "arguments": {"document_id": str(doc.id), "content": new_content},
        },
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["success"] is True
    assert text_data["document_id"] == str(doc.id)

    # Verify the document was actually updated
    await db_session.refresh(doc)
    content = json.loads(doc.content)
    assert content["markdown"] == new_content


@pytest.mark.asyncio
async def test_edit_document_not_editable(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test edit_document tool fails when document is not editable by agent."""
    project = test_project["project"]
    token = test_project["api_token"].token
    doc = test_project["root_doc1"]

    # Document has editable_by_agent=False by default
    new_content = "# Updated Content"
    request_data = {
        "jsonrpc": "2.0",
        "id": 17,
        "method": "tools/call",
        "params": {
            "name": "edit_document",
            "arguments": {"document_id": str(doc.id), "content": new_content},
        },
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "not editable by agents" in data["error"]["message"]


@pytest.mark.asyncio
async def test_create_document_tool(
    client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession
) -> None:
    """Test create_document tool."""
    project = test_project["project"]
    token = test_project["api_token"].token

    request_data = {
        "jsonrpc": "2.0",
        "id": 18,
        "method": "tools/call",
        "params": {
            "name": "create_document",
            "arguments": {
                "title": "New AI Document",
                "type": "markdown",
                "content": "# AI Generated\n\nThis document was created by an AI agent.",
            },
        },
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["success"] is True
    assert "document_id" in text_data

    # Verify the document was created
    doc_id = UUID(text_data["document_id"])
    result = await db_session.execute(select(Document).where(Document.id == doc_id))
    new_doc = result.scalar_one_or_none()
    assert new_doc is not None
    assert new_doc.name == "New AI Document"
    assert new_doc.type == DocumentType.MARKDOWN
    assert new_doc.editable_by_agent is True  # Should be True by default for AI-created docs
    content = json.loads(new_doc.content)
    assert "AI Generated" in content["markdown"]


@pytest.mark.asyncio
async def test_create_document_invalid_type(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test create_document tool with invalid document type."""
    project = test_project["project"]
    token = test_project["api_token"].token

    request_data = {
        "jsonrpc": "2.0",
        "id": 19,
        "method": "tools/call",
        "params": {
            "name": "create_document",
            "arguments": {"title": "Invalid Doc", "type": "invalid_type", "content": "Content"},
        },
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Invalid document type" in data["error"]["message"]


@pytest.mark.asyncio
async def test_edit_document_invalid_id(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test edit_document with invalid document ID format."""
    project = test_project["project"]
    token = test_project["api_token"].token

    request_data = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "edit_document",
            "arguments": {"document_id": "not-a-uuid", "content": "New content"},
        },
    }

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data, headers=get_auth_headers(token))

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Invalid document ID format" in data["error"]["message"]


# ============================================================================
# Authentication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_auth_missing_token(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test that missing authorization header returns 401."""
    project = test_project["project"]
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    response = await client_with_db.post(f"/api/mcp/{project.id}", json=request_data)

    assert response.status_code == 401
    assert "Authorization header required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_invalid_format(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test that invalid authorization header format returns 401."""
    project = test_project["project"]
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    # Missing "Bearer" prefix
    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers={"Authorization": "test_token_123456"}
    )

    assert response.status_code == 401
    assert "Invalid authorization header format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_invalid_token(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test that invalid token returns 401."""
    project = test_project["project"]
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers("invalid_token_does_not_exist")
    )

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_deleted_token(client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession) -> None:
    """Test that deleted (revoked) token returns 401."""
    project = test_project["project"]
    user = test_project["user"]

    # Create a new token and immediately soft delete it
    deleted_token = ApiToken(
        name="Deleted Token",
        user_id=user.id,
        token="deleted_token_123",
        deleted_at=datetime.now(timezone.utc)
    )
    db_session.add(deleted_token)
    await db_session.commit()

    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers("deleted_token_123")
    )

    assert response.status_code == 401
    assert "Token has been revoked" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_no_project_access(client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession) -> None:
    """Test that user without project access returns 403."""
    # Create another user with a token but not in the project's team
    other_user = User(username="otheruser", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    other_token = ApiToken(
        name="Other Token",
        user_id=other_user.id,
        token="other_user_token_123"
    )
    db_session.add(other_token)
    await db_session.commit()

    project = test_project["project"]
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers("other_user_token_123")
    )

    assert response.status_code == 403
    assert "don't have access to this project" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_valid_token_with_access(client_with_db: AsyncClient, test_project: dict) -> None:
    """Test that valid token with project access succeeds."""
    project = test_project["project"]
    token = test_project["api_token"].token
    request_data = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["protocolVersion"] == "2024-11-05"


@pytest.mark.asyncio
async def test_extract_images_from_markdown() -> None:
    """Test extracting base64 images from markdown."""
    markdown = (
        "# Document with images\n\n"
        "Here is an image: ![alt text](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)\n\n"
        "And another: ![second image](data:image/jpeg;base64,/9j/4AAQSkZJRg==)\n\n"
        "Regular text here."
    )

    modified_markdown, images = extract_images_from_markdown(markdown)

    # Check that images were extracted
    assert len(images) == 2

    # Check first image (new format uses 'caption' instead of 'alt')
    assert images[0]["caption"] == "alt text"
    assert images[0]["mime_type"] == "png"
    assert images[0]["data"] == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    # Check second image
    assert images[1]["caption"] == "second image"
    assert images[1]["mime_type"] == "jpeg"
    assert images[1]["data"] == "/9j/4AAQSkZJRg=="

    # Check that markdown has placeholders
    assert "[image:0]" in modified_markdown
    assert "[image:1]" in modified_markdown
    assert "data:image/png;base64" not in modified_markdown
    assert "data:image/jpeg;base64" not in modified_markdown


@pytest.mark.asyncio
async def test_restore_images_to_markdown() -> None:
    """Test restoring base64 images from placeholders."""

    markdown = (
        "# Document with placeholders\n\n"
        "Here is an image: [image:0]\n\n"
        "And another: [image:1]\n\n"
        "Regular text here."
    )

    # Test with new format (caption/title)
    images = [
        {
            "caption": "alt text",
            "mime_type": "png",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        },
        {
            "caption": "second image",
            "mime_type": "jpeg",
            "data": "/9j/4AAQSkZJRg==",
        },
    ]

    restored_markdown = restore_images_to_markdown(markdown, images)

    # Check that placeholders were replaced with actual images
    assert "[image:0]" not in restored_markdown
    assert "[image:1]" not in restored_markdown
    assert "![alt text](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)" in restored_markdown
    assert "![second image](data:image/jpeg;base64,/9j/4AAQSkZJRg==)" in restored_markdown


@pytest.mark.asyncio
async def test_extract_images_with_title_attribute() -> None:
    """Test extracting base64 images with title attribute from markdown."""
    markdown = (
        "# Document with images\n\n"
        '![caption text](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg== "title text")\n\n'
        "Regular text here."
    )

    modified_markdown, images = extract_images_from_markdown(markdown)

    # Check that image was extracted with both caption and title
    assert len(images) == 1
    assert images[0]["caption"] == "caption text"
    assert images[0]["title"] == "title text"
    assert images[0]["mime_type"] == "png"

    # Check that markdown has placeholder
    assert "[image:0]" in modified_markdown
    assert "data:image/png;base64" not in modified_markdown

    # Test restoration
    restored = restore_images_to_markdown(modified_markdown, images)
    assert '![caption text](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg== "title text")' in restored


@pytest.mark.asyncio
async def test_get_document_with_base64_images(
    client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession
) -> None:
    """Test get_document extracts base64 images and returns them separately."""
    project = test_project["project"]
    token = test_project["api_token"].token

    # Create markdown document with base64 images
    markdown_content = (
        "# Document with images\n\n"
        "Here is an image: ![test image](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)\n\n"
        "Regular text here."
    )

    doc = Document(
        name="Image Document",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content=json.dumps({"markdown": markdown_content}),
        parent_id=None,
        order=10,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    request_data = {
        "jsonrpc": "2.0",
        "id": 100,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(doc.id)}},
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()

    content_blocks = data["result"]["content"]

    # Should have: title (text), markdown with placeholders (text), image (image)
    assert len(content_blocks) == 3

    # First block: title
    assert content_blocks[0]["type"] == "text"
    assert "Image Document" in content_blocks[0]["text"]

    # Second block: markdown with placeholder
    assert content_blocks[1]["type"] == "text"
    assert "[image:0]" in content_blocks[1]["text"]
    assert "data:image/png;base64" not in content_blocks[1]["text"]

    # Third block: image
    assert content_blocks[2]["type"] == "image"
    assert content_blocks[2]["data"] == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    assert content_blocks[2]["mimeType"] == "image/png"

    # Verify images were saved to document content
    await db_session.refresh(doc)
    saved_content = json.loads(doc.content)
    assert "images" in saved_content
    assert len(saved_content["images"]) == 1
    assert saved_content["images"][0]["caption"] == "test image"


@pytest.mark.asyncio
async def test_edit_document_with_image_placeholders(
    client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession
) -> None:
    """Test edit_document restores images from placeholders."""
    project = test_project["project"]
    token = test_project["api_token"].token

    # Create markdown document with base64 images
    markdown_content = (
        "# Original document\n\n"
        "Image: ![original](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)"
    )

    images = [
        {
            "alt": "original",
            "mime_type": "png",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        }
    ]

    doc = Document(
        name="Editable Image Document",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content=json.dumps({"markdown": markdown_content, "images": images}),
        parent_id=None,
        order=11,
        editable_by_agent=True,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    # Edit document with placeholder
    new_content = (
        "# Updated document\n\n"
        "Image is still here: [image:0]\n\n"
        "With some new text."
    )

    request_data = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "edit_document",
            "arguments": {"document_id": str(doc.id), "content": new_content},
        },
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["success"] is True

    # Verify the document content was updated with restored image
    await db_session.refresh(doc)
    saved_content = json.loads(doc.content)
    assert "markdown" in saved_content
    restored_markdown = saved_content["markdown"]

    # Check that placeholder was replaced with actual image
    assert "[image:0]" not in restored_markdown
    assert "![original](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==)" in restored_markdown
    assert "# Updated document" in restored_markdown
    assert "With some new text" in restored_markdown


@pytest.mark.asyncio
async def test_markdown_without_images(
    client_with_db: AsyncClient, test_project: dict, db_session: AsyncSession
) -> None:
    """Test get_document with markdown that has no images."""
    project = test_project["project"]
    token = test_project["api_token"].token

    markdown_content = "# Simple document\n\nNo images here, just text."

    doc = Document(
        name="No Images Document",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content=json.dumps({"markdown": markdown_content}),
        parent_id=None,
        order=12,
    )
    db_session.add(doc)
    await db_session.commit()
    await db_session.refresh(doc)

    request_data = {
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {"name": "get_document", "arguments": {"id": str(doc.id)}},
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers=get_auth_headers(token)
    )

    assert response.status_code == 200
    data = response.json()

    content_blocks = data["result"]["content"]

    # Should have only: title (text), markdown (text) - no images
    assert len(content_blocks) == 2
    assert content_blocks[0]["type"] == "text"
    assert "No Images Document" in content_blocks[0]["text"]
    assert content_blocks[1]["type"] == "text"
    assert "No images here" in content_blocks[1]["text"]
