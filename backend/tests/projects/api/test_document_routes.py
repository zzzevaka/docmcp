"""Test document routes."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.library.models import Category, Template, TemplateType, TemplateVisibility
from app.projects.models import Document, DocumentType, Project
from app.users.models import Team, User


@pytest.mark.asyncio
async def test_add_template_hierarchy_creates_all_documents(
    db_session: AsyncSession, client: AsyncClient
):
    """Test that adding a template with children creates all documents in the hierarchy."""
    # Get test user
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    # Create team
    team = Team(name="Hierarchy Test Team")
    db_session.add(team)
    await db_session.flush()

    user.teams = [team]
    await db_session.flush()

    # Create project
    project = Project(name="Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    # Create category
    category = Category(name="Hierarchy Test Category", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    # Create template hierarchy
    # Root template
    root_template = Template(
        name="Root Template",
        team_id=team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Root content"}',
        parent_id=None,
        order=0,
    )
    db_session.add(root_template)
    await db_session.flush()

    # Child templates
    child1 = Template(
        name="Child 1",
        team_id=team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Child 1 content"}',
        parent_id=root_template.id,
        order=0,
    )
    child2 = Template(
        name="Child 2",
        team_id=team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Child 2 content"}',
        parent_id=root_template.id,
        order=1,
    )
    db_session.add(child1)
    db_session.add(child2)
    await db_session.flush()

    # Grandchild template
    grandchild = Template(
        name="Grandchild",
        team_id=team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Grandchild content"}',
        parent_id=child1.id,
        order=0,
    )
    db_session.add(grandchild)
    await db_session.commit()

    # Check initial document count
    initial_docs_response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert initial_docs_response.status_code == 200
    initial_docs = initial_docs_response.json()
    initial_count = len(initial_docs)

    # Add template to project
    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{root_template.id}"
    )
    assert response.status_code == 201, f"Failed with: {response.text}"
    root_doc = response.json()
    assert root_doc["name"] == "Root Template"
    assert root_doc["parent_id"] is None

    # Verify all documents were created
    final_docs_response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert final_docs_response.status_code == 200
    final_docs = final_docs_response.json()

    # Should have 4 more documents (root + 2 children + 1 grandchild)
    assert len(final_docs) == initial_count + 4

    # Verify hierarchy structure
    root_doc_full = next((d for d in final_docs if d["name"] == "Root Template"), None)
    assert root_doc_full is not None
    assert root_doc_full["parent_id"] is None

    # Check children
    children_docs = [d for d in final_docs if d["parent_id"] == root_doc_full["id"]]
    assert len(children_docs) == 2
    child_names = {d["name"] for d in children_docs}
    assert "Child 1" in child_names
    assert "Child 2" in child_names

    # Check grandchild
    child1_doc = next((d for d in children_docs if d["name"] == "Child 1"), None)
    assert child1_doc is not None

    grandchildren_docs = [d for d in final_docs if d["parent_id"] == child1_doc["id"]]
    assert len(grandchildren_docs) == 1
    assert grandchildren_docs[0]["name"] == "Grandchild"

    # Verify order is preserved
    sorted_children = sorted(children_docs, key=lambda d: d["order"])
    assert sorted_children[0]["name"] == "Child 1"
    assert sorted_children[1]["name"] == "Child 2"


@pytest.mark.asyncio
async def test_add_template_without_children_creates_only_root(
    db_session: AsyncSession, client: AsyncClient
):
    """Test that adding a template without children creates only one document."""
    # Get test user
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    # Create team
    team = Team(name="Single Test Team")
    db_session.add(team)
    await db_session.flush()

    user.teams = [team]
    await db_session.flush()

    # Create project
    project = Project(name="Test Project 2", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    # Create category
    category = Category(name="Single Test Category", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    # Create single template without children
    template = Template(
        name="Single Template",
        team_id=team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Single content"}',
        parent_id=None,
        order=0,
    )
    db_session.add(template)
    await db_session.commit()

    # Add template to project
    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{template.id}"
    )
    assert response.status_code == 201
    doc = response.json()
    assert doc["name"] == "Single Template"

    # Verify only one document was created
    docs_response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert docs_response.status_code == 200
    docs = docs_response.json()
    assert len(docs) == 1


@pytest.mark.asyncio
async def test_list_documents(db_session: AsyncSession, client: AsyncClient):
    """Test listing documents for a project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="List Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="List Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    # Create documents
    doc1 = Document(
        name="Doc 1",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content 1"}',
    )
    doc2 = Document(
        name="Doc 2",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content 2"}',
    )
    db_session.add(doc1)
    db_session.add(doc2)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 2
    assert docs[0]["content"]["markdown"] == "Content 1"


@pytest.mark.asyncio
async def test_list_documents_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test listing documents for non-existent project."""
    from uuid import uuid4

    fake_id = uuid4()
    response = await client.get(f"/api/v1/projects/{fake_id}/documents/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_documents_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test listing documents when user is not a team member."""
    # Create team without adding user
    team = Team(name="Other Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_document(db_session: AsyncSession, client: AsyncClient):
    """Test getting a single document."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Get Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Get Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Test Doc",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Test content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{project.id}/documents/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Doc"
    assert data["content"]["markdown"] == "Test content"


@pytest.mark.asyncio
async def test_get_document_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test getting non-existent document."""
    from uuid import uuid4

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Get NF Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Get NF Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    fake_doc_id = uuid4()
    response = await client.get(f"/api/v1/projects/{project.id}/documents/{fake_doc_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_document(db_session: AsyncSession, client: AsyncClient):
    """Test creating a new document."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Create Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Create Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    payload = {
        "name": "New Document",
        "type": "markdown",
        "content": {"markdown": "New content"},
    }

    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/", json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Document"
    assert data["content"]["markdown"] == "New content"


@pytest.mark.asyncio
async def test_create_document_with_parent(db_session: AsyncSession, client: AsyncClient):
    """Test creating a document with a parent."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Create Parent Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Create Parent Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    parent_doc = Document(
        name="Parent",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Parent"}',
    )
    db_session.add(parent_doc)
    await db_session.commit()

    payload = {
        "name": "Child Document",
        "type": "markdown",
        "content": {"markdown": "Child content"},
        "parent_id": str(parent_doc.id),
    }

    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/", json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == str(parent_doc.id)


@pytest.mark.asyncio
async def test_create_document_invalid_parent(db_session: AsyncSession, client: AsyncClient):
    """Test creating a document with invalid parent."""
    from uuid import uuid4

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Create Invalid Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Create Invalid Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    payload = {
        "name": "Child Document",
        "type": "markdown",
        "content": {"markdown": "Child content"},
        "parent_id": str(uuid4()),
    }

    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/", json=payload
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_document(db_session: AsyncSession, client: AsyncClient):
    """Test updating a document."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Update Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Update Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Original Name",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Original content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    payload = {
        "name": "Updated Name",
        "content": {"markdown": "Updated content"},
    }

    response = await client.put(
        f"/api/v1/projects/{project.id}/documents/{doc.id}", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["content"]["markdown"] == "Updated content"


@pytest.mark.asyncio
async def test_update_document_parent_id(db_session: AsyncSession, client: AsyncClient):
    """Test updating a document's parent."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Update Parent Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Update Parent Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    parent1 = Document(
        name="Parent 1",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Parent 1"}',
    )
    parent2 = Document(
        name="Parent 2",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Parent 2"}',
    )
    child = Document(
        name="Child",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Child"}',
        parent_id=parent1.id,
    )
    db_session.add(parent1)
    db_session.add(parent2)
    db_session.add(child)
    await db_session.commit()

    payload = {"parent_id": str(parent2.id)}

    response = await client.put(
        f"/api/v1/projects/{project.id}/documents/{child.id}", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parent_id"] == str(parent2.id)


@pytest.mark.asyncio
async def test_update_document_circular_reference(db_session: AsyncSession, client: AsyncClient):
    """Test preventing circular parent reference."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Circular Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Circular Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Self Doc",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Self"}',
    )
    db_session.add(doc)
    await db_session.commit()

    payload = {"parent_id": str(doc.id)}

    response = await client.put(
        f"/api/v1/projects/{project.id}/documents/{doc.id}", json=payload
    )
    assert response.status_code == 400
    assert "own parent" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_document_order(db_session: AsyncSession, client: AsyncClient):
    """Test updating a document's order."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Order Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Order Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Doc",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Doc"}',
        order=0,
    )
    db_session.add(doc)
    await db_session.commit()

    payload = {"order": 5}

    response = await client.put(
        f"/api/v1/projects/{project.id}/documents/{doc.id}", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["order"] == 5


@pytest.mark.asyncio
async def test_delete_document(db_session: AsyncSession, client: AsyncClient):
    """Test deleting a document."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Delete Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Delete Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="To Delete",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Delete me"}',
    )
    db_session.add(doc)
    await db_session.commit()

    response = await client.delete(f"/api/v1/projects/{project.id}/documents/{doc.id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/projects/{project.id}/documents/{doc.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test deleting non-existent document."""
    from uuid import uuid4

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Delete NF Test Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Delete NF Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    fake_doc_id = uuid4()
    response = await client.delete(f"/api/v1/projects/{project.id}/documents/{fake_doc_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_from_template_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test creating from non-existent template."""
    from uuid import uuid4

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Template NF Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Template NF Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    fake_template_id = uuid4()
    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{fake_template_id}"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_from_template_private_not_owner(
    db_session: AsyncSession, client: AsyncClient
):
    """Test creating from private template when not owner."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    # Create another user
    other_user = User(username="otheruser", email="other@example.com")
    db_session.add(other_user)
    await db_session.flush()

    team = Team(name="Private Template Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Private Template Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    category = Category(name="Private Cat", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    # Create private template owned by other user
    template = Template(
        name="Private Template",
        team_id=team.id,
        user_id=other_user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PRIVATE,
        content='{"markdown": "Private"}',
    )
    db_session.add(template)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{template.id}"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_from_template_team_not_member(
    db_session: AsyncSession, client: AsyncClient
):
    """Test creating from team template when not team member."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    user_team = Team(name="User Team")
    db_session.add(user_team)
    await db_session.flush()
    user.teams = [user_team]
    await db_session.flush()

    other_team = Team(name="Other Team")
    db_session.add(other_team)
    await db_session.flush()

    project = Project(name="Team Template Project", team_id=user_team.id)
    db_session.add(project)
    await db_session.flush()

    category = Category(name="Team Cat", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    # Create team template in other team
    template = Template(
        name="Team Template",
        team_id=other_team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.TEAM,
        content='{"markdown": "Team"}',
    )
    db_session.add(template)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{template.id}"
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_document_wrong_project(db_session: AsyncSession, client: AsyncClient):
    """Test getting document that belongs to different project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Wrong Project Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project1 = Project(name="Project 1", team_id=team.id)
    project2 = Project(name="Project 2", team_id=team.id)
    db_session.add(project1)
    db_session.add(project2)
    await db_session.flush()

    doc = Document(
        name="Doc in Project 1",
        project_id=project1.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    # Try to get doc from project1 using project2's ID
    response = await client.get(f"/api/v1/projects/{project2.id}/documents/{doc.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_document_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test getting document when project doesn't exist."""
    from uuid import uuid4

    fake_project_id = uuid4()
    fake_doc_id = uuid4()
    response = await client.get(f"/api/v1/projects/{fake_project_id}/documents/{fake_doc_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_document_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test getting document when user is not team member."""
    team = Team(name="Other Get Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Get Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Other Doc",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{project.id}/documents/{doc.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_document_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test creating document when project doesn't exist."""
    from uuid import uuid4

    fake_project_id = uuid4()
    payload = {
        "name": "New Doc",
        "type": "markdown",
        "content": {"markdown": "Content"},
    }

    response = await client.post(f"/api/v1/projects/{fake_project_id}/documents/", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_document_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test creating document when user is not team member."""
    team = Team(name="Other Create Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Create Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    payload = {
        "name": "New Doc",
        "type": "markdown",
        "content": {"markdown": "Content"},
    }

    response = await client.post(f"/api/v1/projects/{project.id}/documents/", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_document_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test updating document when project doesn't exist."""
    from uuid import uuid4

    fake_project_id = uuid4()
    fake_doc_id = uuid4()
    payload = {"name": "Updated"}

    response = await client.put(
        f"/api/v1/projects/{fake_project_id}/documents/{fake_doc_id}", json=payload
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_document_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test updating non-existent document."""
    from uuid import uuid4

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Update NF Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project = Project(name="Update NF Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    fake_doc_id = uuid4()
    payload = {"name": "Updated"}

    response = await client.put(
        f"/api/v1/projects/{project.id}/documents/{fake_doc_id}", json=payload
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_document_wrong_project(db_session: AsyncSession, client: AsyncClient):
    """Test updating document that belongs to different project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Update Wrong Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project1 = Project(name="Project 1", team_id=team.id)
    project2 = Project(name="Project 2", team_id=team.id)
    db_session.add(project1)
    db_session.add(project2)
    await db_session.flush()

    doc = Document(
        name="Doc in Project 1",
        project_id=project1.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    payload = {"name": "Updated"}

    # Try to update doc from project1 using project2's ID
    response = await client.put(
        f"/api/v1/projects/{project2.id}/documents/{doc.id}", json=payload
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_document_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test updating document when user is not team member."""
    team = Team(name="Other Update Team2")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Update Project2", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Other Doc",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    payload = {"name": "Updated"}

    response = await client.put(
        f"/api/v1/projects/{project.id}/documents/{doc.id}", json=payload
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_document_invalid_parent_project(db_session: AsyncSession, client: AsyncClient):
    """Test updating document with parent from different project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Invalid Parent Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project1 = Project(name="Project 1", team_id=team.id)
    project2 = Project(name="Project 2", team_id=team.id)
    db_session.add(project1)
    db_session.add(project2)
    await db_session.flush()

    parent = Document(
        name="Parent in Project 1",
        project_id=project1.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Parent"}',
    )
    child = Document(
        name="Child in Project 2",
        project_id=project2.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Child"}',
    )
    db_session.add(parent)
    db_session.add(child)
    await db_session.commit()

    # Try to set parent from project1 to child in project2
    payload = {"parent_id": str(parent.id)}

    response = await client.put(
        f"/api/v1/projects/{project2.id}/documents/{child.id}", json=payload
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_document_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test deleting document when project doesn't exist."""
    from uuid import uuid4

    fake_project_id = uuid4()
    fake_doc_id = uuid4()

    response = await client.delete(f"/api/v1/projects/{fake_project_id}/documents/{fake_doc_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_wrong_project(db_session: AsyncSession, client: AsyncClient):
    """Test deleting document that belongs to different project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Delete Wrong Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    project1 = Project(name="Project 1", team_id=team.id)
    project2 = Project(name="Project 2", team_id=team.id)
    db_session.add(project1)
    db_session.add(project2)
    await db_session.flush()

    doc = Document(
        name="Doc in Project 1",
        project_id=project1.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    # Try to delete doc from project1 using project2's ID
    response = await client.delete(f"/api/v1/projects/{project2.id}/documents/{doc.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test deleting document when user is not team member."""
    team = Team(name="Other Delete Team2")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Delete Project2", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    doc = Document(
        name="Other Doc",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Content"}',
    )
    db_session.add(doc)
    await db_session.commit()

    response = await client.delete(f"/api/v1/projects/{project.id}/documents/{doc.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_from_template_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test creating from template when project doesn't exist."""
    from uuid import uuid4

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Template PNF Team")
    db_session.add(team)
    await db_session.flush()
    user.teams = [team]
    await db_session.flush()

    category = Category(name="PNF Cat", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    template = Template(
        name="Template",
        team_id=team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Content"}',
    )
    db_session.add(template)
    await db_session.commit()

    fake_project_id = uuid4()
    response = await client.post(
        f"/api/v1/projects/{fake_project_id}/documents/from-template/{template.id}"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_from_template_project_not_team_member(
    db_session: AsyncSession, client: AsyncClient
):
    """Test creating from template when user is not project team member."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    user_team = Team(name="User Template Team")
    db_session.add(user_team)
    await db_session.flush()
    user.teams = [user_team]
    await db_session.flush()

    other_team = Team(name="Other Project Team")
    db_session.add(other_team)
    await db_session.flush()

    project = Project(name="Other Project", team_id=other_team.id)
    db_session.add(project)
    await db_session.flush()

    category = Category(name="PNM Cat", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    template = Template(
        name="Template",
        team_id=user_team.id,
        user_id=user.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Content"}',
    )
    db_session.add(template)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{template.id}"
    )
    assert response.status_code == 403
