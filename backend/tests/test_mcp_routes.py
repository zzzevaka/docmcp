"""Tests for MCP routes."""

import json
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.projects.models import Document, DocumentType, Project
from app.users.models import Team, User


@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client_with_db(db_session: AsyncSession):
    """Create test client with database session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_project(db_session: AsyncSession):
    """Create a test project with documents."""
    # Create user and team
    user = User(username="testuser", email="test@example.com")
    team = Team(name="Test Team")
    team.members.append(user)
    db_session.add(team)
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
        content=json.dumps({
            "elements": [],
            "appState": {},
            "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="  # 1x1 transparent PNG
        }),
        parent_id=None,
        order=1,
    )
    db_session.add(root_doc2)
    await db_session.flush()

    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(root_doc1)
    await db_session.refresh(child_doc1)
    await db_session.refresh(child_doc2)
    await db_session.refresh(root_doc2)

    return {
        "project": project,
        "root_doc1": root_doc1,
        "child_doc1": child_doc1,
        "child_doc2": child_doc2,
        "root_doc2": root_doc2,
    }


@pytest.mark.asyncio
async def test_initialize(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test MCP initialize method."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
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
async def test_tools_list(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test MCP tools/list method."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["id"] == 2
    assert "result" in data
    assert "tools" in data["result"]
    assert len(data["result"]["tools"]) == 3

    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    assert "list_documents" in tool_names
    assert "search_documents" in tool_names
    assert "get_document" in tool_names


@pytest.mark.asyncio
async def test_list_documents_tool(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test list_documents tool."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_documents",
            "arguments": {}
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

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
    assert "descendants" in doc1
    assert len(doc1["descendants"]) == 2


@pytest.mark.asyncio
async def test_search_documents_tool(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test search_documents tool."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "search_documents",
            "arguments": {
                "query": "installation"
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

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
async def test_get_document_tool(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test get_document tool."""
    project = test_project["project"]
    doc = test_project["root_doc1"]

    request_data = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "get_document",
            "arguments": {
                "id": str(doc.id)
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

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
async def test_get_document_whiteboard(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test get_document with whiteboard document returns base64 image."""
    project = test_project["project"]
    doc = test_project["root_doc2"]

    request_data = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "get_document",
            "arguments": {
                "id": str(doc.id)
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

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
async def test_unknown_method(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test unknown method returns error."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "unknown_method",
        "params": {}
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

    # Unknown method should return HTTP 400 or JSON-RPC error
    if response.status_code == 200:
        data = response.json()
        assert "error" in data
    else:
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_invalid_json(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test invalid JSON returns error."""
    project = test_project["project"]

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        content=b"invalid json"
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_nonexistent_project(
    client_with_db: AsyncClient,
) -> None:
    """Test with nonexistent project."""
    fake_uuid = uuid4()
    request_data = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "list_documents",
            "arguments": {}
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{fake_uuid}",
        json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    # Should return error in JSON-RPC format
    assert "error" in data
    assert data["error"]["code"] == -32603


@pytest.mark.asyncio
async def test_empty_project(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """Test list_documents with project that has no documents."""
    # Create empty project
    team = Team(name="Empty Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Empty Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    request_data = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {
            "name": "list_documents",
            "arguments": {}
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
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
    # Create project with whiteboard document without image
    team = Team(name="Test Team")
    db_session.add(team)
    await db_session.flush()

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
    await db_session.commit()
    await db_session.refresh(doc)

    request_data = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "get_document",
            "arguments": {
                "id": str(doc.id)
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
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
async def test_unknown_tool(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test calling unknown tool."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "unknown_tool",
            "arguments": {}
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Unknown tool" in data["error"]["message"]


@pytest.mark.asyncio
async def test_get_document_invalid_id(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test get_document with invalid document ID format."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
            "name": "get_document",
            "arguments": {
                "id": "not-a-valid-uuid"
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Invalid document ID format" in data["error"]["message"]


@pytest.mark.asyncio
async def test_get_nonexistent_document(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test get_document with valid UUID but non-existent document."""
    project = test_project["project"]
    fake_doc_id = uuid4()

    request_data = {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {
            "name": "get_document",
            "arguments": {
                "id": str(fake_doc_id)
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    # Should return error
    assert "error" in data
    assert "Document not found" in data["error"]["message"]


@pytest.mark.asyncio
async def test_search_no_results(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test search_documents with query that matches nothing."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {
            "name": "search_documents",
            "arguments": {
                "query": "xyzabc123nonexistent"
            }
        }
    }

    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    text_data = json.loads(data["result"]["content"][0]["text"])
    assert text_data["query"] == "xyzabc123nonexistent"
    assert text_data["results"] == []


@pytest.mark.asyncio
async def test_sse_support(
    client_with_db: AsyncClient, test_project: dict
) -> None:
    """Test SSE (Server-Sent Events) support."""
    project = test_project["project"]
    request_data = {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "initialize",
        "params": {}
    }

    # Send request with SSE Accept header
    response = await client_with_db.post(
        f"/api/mcp/{project.id}",
        json=request_data,
        headers={"Accept": "text/event-stream"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Check SSE format
    content = response.text
    assert content.startswith("data: ")
    assert content.endswith("\n\n")
