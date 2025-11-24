"""Test adding templates with hierarchy to projects."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.library.models import Category, Template, TemplateType, TemplateVisibility
from app.projects.models import Project
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
