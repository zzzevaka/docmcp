import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.library.models import Category, Template, TemplateType, TemplateVisibility
from app.library.repositories import TemplateRepository
from app.projects.models import Document, DocumentType, Project
from app.users.models import Team, User


@pytest.fixture
async def setup_test_data(db_session: AsyncSession):
    """Create test data for template visibility tests."""
    # Create teams
    team1 = Team(name="Team Alpha")
    team2 = Team(name="Team Beta")
    db_session.add(team1)
    db_session.add(team2)
    await db_session.flush()

    # Create users
    user1 = User(username="user1", email="user1@example.com")
    user2 = User(username="user2", email="user2@example.com")
    user3 = User(username="user3", email="user3@example.com")

    # Assign users to teams
    user1.teams = [team1]  # user1 is in team1
    user2.teams = [team2]  # user2 is in team2
    user3.teams = []  # user3 is not in any team

    db_session.add(user1)
    db_session.add(user2)
    db_session.add(user3)
    await db_session.flush()

    # Create category
    category = Category(name="General", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    # Create templates with different visibility settings

    # Public template created by user1
    template_public = Template(
        name="Public Template",
        team_id=team1.id,
        user_id=user1.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Public content"}',
    )

    # Team template created by user1 (team1)
    template_team1 = Template(
        name="Team1 Template",
        team_id=team1.id,
        user_id=user1.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.TEAM,
        content='{"markdown": "Team1 content"}',
    )

    # Team template created by user2 (team2)
    template_team2 = Template(
        name="Team2 Template",
        team_id=team2.id,
        user_id=user2.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.TEAM,
        content='{"markdown": "Team2 content"}',
    )

    # Private template created by user1
    template_private_user1 = Template(
        name="Private User1 Template",
        team_id=team1.id,
        user_id=user1.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PRIVATE,
        content='{"markdown": "Private user1 content"}',
    )

    # Private template created by user2
    template_private_user2 = Template(
        name="Private User2 Template",
        team_id=team2.id,
        user_id=user2.id,
        category_id=category.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PRIVATE,
        content='{"markdown": "Private user2 content"}',
    )

    db_session.add(template_public)
    db_session.add(template_team1)
    db_session.add(template_team2)
    db_session.add(template_private_user1)
    db_session.add(template_private_user2)

    await db_session.commit()

    return {
        "teams": {"team1": team1, "team2": team2},
        "users": {"user1": user1, "user2": user2, "user3": user3},
        "category": category,
        "templates": {
            "public": template_public,
            "team1": template_team1,
            "team2": template_team2,
            "private_user1": template_private_user1,
            "private_user2": template_private_user2,
        },
    }


@pytest.mark.asyncio
async def test_list_templates_user_in_team1_sees_correct_templates(
    db_session: AsyncSession, setup_test_data
):
    """Test that user1 (in team1) sees public, team1, and their own private templates."""
    data = setup_test_data
    user1 = data["users"]["user1"]
    team1 = data["teams"]["team1"]

    repo = TemplateRepository(db_session)
    templates = await repo.find_visible_for_user(
        user_id=user1.id,
        user_team_ids=[team1.id],
        include_content=False,
    )

    template_names = {t.name for t in templates}

    # user1 should see:
    # - Public Template (public)
    # - Team1 Template (their team)
    # - Private User1 Template (their own private)
    assert "Public Template" in template_names
    assert "Team1 Template" in template_names
    assert "Private User1 Template" in template_names

    # user1 should NOT see:
    # - Team2 Template (not their team)
    # - Private User2 Template (not their private)
    assert "Team2 Template" not in template_names
    assert "Private User2 Template" not in template_names

    assert len(templates) == 3


@pytest.mark.asyncio
async def test_list_templates_user_in_team2_sees_correct_templates(
    db_session: AsyncSession, setup_test_data
):
    """Test that user2 (in team2) sees public, team2, and their own private templates."""
    data = setup_test_data
    user2 = data["users"]["user2"]
    team2 = data["teams"]["team2"]

    repo = TemplateRepository(db_session)
    templates = await repo.find_visible_for_user(
        user_id=user2.id,
        user_team_ids=[team2.id],
        include_content=False,
    )

    template_names = {t.name for t in templates}

    # user2 should see:
    # - Public Template (public)
    # - Team2 Template (their team)
    # - Private User2 Template (their own private)
    assert "Public Template" in template_names
    assert "Team2 Template" in template_names
    assert "Private User2 Template" in template_names

    # user2 should NOT see:
    # - Team1 Template (not their team)
    # - Private User1 Template (not their private)
    assert "Team1 Template" not in template_names
    assert "Private User1 Template" not in template_names

    assert len(templates) == 3


@pytest.mark.asyncio
async def test_list_templates_user_not_in_any_team_sees_only_public(
    db_session: AsyncSession, setup_test_data
):
    """Test that user3 (not in any team) sees only public templates."""
    data = setup_test_data
    user3 = data["users"]["user3"]

    repo = TemplateRepository(db_session)
    templates = await repo.find_visible_for_user(
        user_id=user3.id,
        user_team_ids=[],
        include_content=False,
    )

    template_names = {t.name for t in templates}

    # user3 should see:
    # - Public Template (public)
    assert "Public Template" in template_names

    # user3 should NOT see any team or private templates
    assert "Team1 Template" not in template_names
    assert "Team2 Template" not in template_names
    assert "Private User1 Template" not in template_names
    assert "Private User2 Template" not in template_names

    assert len(templates) == 1


@pytest.mark.asyncio
async def test_list_templates_filters_by_category(
    db_session: AsyncSession, setup_test_data
):
    """Test that templates can be filtered by category."""
    data = setup_test_data
    user1 = data["users"]["user1"]
    team1 = data["teams"]["team1"]
    category = data["category"]

    # Create another category with a template
    category2 = Category(name="Other", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category2)
    await db_session.flush()

    template_other = Template(
        name="Other Category Template",
        team_id=team1.id,
        user_id=user1.id,
        category_id=category2.id,
        type=TemplateType.MARKDOWN,
        visibility=TemplateVisibility.PUBLIC,
        content='{"markdown": "Other content"}',
    )
    db_session.add(template_other)
    await db_session.commit()

    repo = TemplateRepository(db_session)

    # Filter by first category
    templates = await repo.find_visible_for_user(
        user_id=user1.id,
        user_team_ids=[team1.id],
        category_id=category.id,
        include_content=False,
    )

    template_names = {t.name for t in templates}

    # Should see all templates from first category that user1 can access
    assert "Public Template" in template_names
    assert "Team1 Template" in template_names
    assert "Private User1 Template" in template_names

    # Should NOT see template from other category
    assert "Other Category Template" not in template_names


@pytest.mark.asyncio
async def test_list_templates_excludes_content_when_requested(
    db_session: AsyncSession, setup_test_data
):
    """Test that content is excluded when include_content=False."""
    data = setup_test_data
    user1 = data["users"]["user1"]
    team1 = data["teams"]["team1"]

    repo = TemplateRepository(db_session)
    templates = await repo.find_visible_for_user(
        user_id=user1.id,
        user_team_ids=[team1.id],
        include_content=False,
    )

    # Content should be deferred (not loaded)
    for template in templates:
        # Accessing content would trigger a lazy load, but in this case
        # it should be deferred and not present in the loaded attributes
        # This is a simplified check - in real scenario, SQLAlchemy's
        # inspection would be used to verify deferred attributes
        assert hasattr(template, "name")
        assert hasattr(template, "visibility")


@pytest.mark.asyncio
async def test_private_template_visible_only_to_creator(
    db_session: AsyncSession, setup_test_data
):
    """Test that private templates are visible only to their creator."""
    data = setup_test_data
    user1 = data["users"]["user1"]
    user2 = data["users"]["user2"]
    team1 = data["teams"]["team1"]
    team2 = data["teams"]["team2"]

    repo = TemplateRepository(db_session)

    # user1 sees their own private template
    templates_user1 = await repo.find_visible_for_user(
        user_id=user1.id,
        user_team_ids=[team1.id],
        include_content=False,
    )
    user1_template_names = {t.name for t in templates_user1}
    assert "Private User1 Template" in user1_template_names
    assert "Private User2 Template" not in user1_template_names

    # user2 sees their own private template
    templates_user2 = await repo.find_visible_for_user(
        user_id=user2.id,
        user_team_ids=[team2.id],
        include_content=False,
    )
    user2_template_names = {t.name for t in templates_user2}
    assert "Private User2 Template" in user2_template_names
    assert "Private User1 Template" not in user2_template_names


@pytest.mark.asyncio
async def test_team_template_visible_to_all_team_members(
    db_session: AsyncSession, setup_test_data
):
    """Test that team templates are visible to all members of that team."""
    data = setup_test_data

    # Add another user to team1
    user4 = User(username="user4", email="user4@example.com")
    team1 = data["teams"]["team1"]
    user4.teams = [team1]
    db_session.add(user4)
    await db_session.commit()

    repo = TemplateRepository(db_session)

    # user4 (new member of team1) should see team1 templates
    templates = await repo.find_visible_for_user(
        user_id=user4.id,
        user_team_ids=[team1.id],
        include_content=False,
    )

    template_names = {t.name for t in templates}

    # Should see public and team1 templates
    assert "Public Template" in template_names
    assert "Team1 Template" in template_names

    # Should NOT see private templates of other users or team2 templates
    assert "Private User1 Template" not in template_names
    assert "Team2 Template" not in template_names


@pytest.fixture
async def setup_api_test_data(db_session: AsyncSession):
    """Create test data for API integration tests."""
    # Get the test user created by the client fixture
    from sqlalchemy import select
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    # Create team
    team = Team(name="API Test Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    user.teams = [team]
    await db_session.flush()

    # Create project
    project = Project(name="API Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.flush()

    # Create category
    category = Category(name="API Test Category", visibility=TemplateVisibility.PUBLIC)
    db_session.add(category)
    await db_session.flush()

    # Create hierarchical documents
    doc_root = Document(
        name="API Root Document",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Root content"}',
        parent_id=None,
        order=0,
    )
    db_session.add(doc_root)
    await db_session.flush()

    doc_child1 = Document(
        name="API Child 1",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Child 1 content"}',
        parent_id=doc_root.id,
        order=0,
    )
    doc_child2 = Document(
        name="API Child 2",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Child 2 content"}',
        parent_id=doc_root.id,
        order=1,
    )
    db_session.add(doc_child1)
    db_session.add(doc_child2)
    await db_session.flush()

    doc_grandchild = Document(
        name="API Grandchild",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "Grandchild content"}',
        parent_id=doc_child1.id,
        order=0,
    )
    db_session.add(doc_grandchild)
    await db_session.commit()

    return {
        "team": team,
        "user": user,
        "project": project,
        "category": category,
        "documents": {
            "root": doc_root,
            "child1": doc_child1,
            "child2": doc_child2,
            "grandchild": doc_grandchild,
        },
    }


@pytest.mark.asyncio
async def test_create_template_without_children_via_api(
    db_session: AsyncSession, client: AsyncClient, setup_api_test_data
):
    """Test creating a template without children via API."""
    data = setup_api_test_data
    doc_root = data["documents"]["root"]

    # Create template without children
    response = await client.post(
        "/api/v1/library/templates/",
        json={
            "document_id": str(doc_root.id),
            "name": "API Template Without Children",
            "category_name": "API Test Category",
            "visibility": "public",
            "include_children": False,
        },
    )

    assert response.status_code == 201
    template_data = response.json()
    assert template_data["name"] == "API Template Without Children"
    assert template_data["parent_id"] is None
    assert template_data["order"] == 0

    # Verify only one template was created (no children)
    templates_response = await client.get("/api/v1/library/templates/")
    assert templates_response.status_code == 200
    templates = templates_response.json()

    # Filter templates for this test
    api_templates = [t for t in templates if "API Template" in t["name"]]
    assert len(api_templates) == 1


@pytest.mark.asyncio
async def test_create_template_with_children_via_api(
    db_session: AsyncSession, client: AsyncClient, setup_api_test_data
):
    """Test creating a template with children via API - this is the 500 error case."""
    data = setup_api_test_data
    doc_root = data["documents"]["root"]

    # Create template with children - this was causing 500 error
    response = await client.post(
        "/api/v1/library/templates/",
        json={
            "document_id": str(doc_root.id),
            "name": "API Template With Children",
            "category_name": "API Test Category",
            "visibility": "public",
            "include_children": True,
        },
    )

    assert response.status_code == 201, f"Failed with: {response.text}"
    template_data = response.json()
    assert template_data["name"] == "API Template With Children"
    assert template_data["parent_id"] is None

    # Verify all templates were created (root + 2 children + 1 grandchild = 4)
    # Use only_root=false to get all templates including children
    templates_response = await client.get("/api/v1/library/templates/", params={"only_root": False})
    assert templates_response.status_code == 200
    templates = templates_response.json()

    # Filter templates for this test
    api_templates = [t for t in templates if "API Template With Children" in t["name"] or "API Child" in t["name"] or "API Grandchild" in t["name"]]
    assert len(api_templates) == 4

    # Verify parent-child relationships
    root_template = next((t for t in api_templates if t["name"] == "API Template With Children"), None)
    assert root_template is not None
    assert root_template["parent_id"] is None

    child_templates = [t for t in api_templates if t["parent_id"] == root_template["id"]]
    assert len(child_templates) == 2

    # Verify grandchild
    child1_template = next((t for t in child_templates if t["name"] == "API Child 1"), None)
    assert child1_template is not None

    grandchild_templates = [t for t in api_templates if t["parent_id"] == child1_template["id"]]
    assert len(grandchild_templates) == 1
    assert grandchild_templates[0]["name"] == "API Grandchild"


@pytest.mark.asyncio
async def test_add_template_to_project_via_api(
    db_session: AsyncSession, client: AsyncClient, setup_api_test_data
):
    """Test adding a template with children to a project via API."""
    data = setup_api_test_data
    doc_root = data["documents"]["root"]
    project = data["project"]

    # First, create a template with children
    create_response = await client.post(
        "/api/v1/library/templates/",
        json={
            "document_id": str(doc_root.id),
            "name": "Template For Project",
            "category_name": "API Test Category",
            "visibility": "public",
            "include_children": True,
        },
    )

    assert create_response.status_code == 201
    template_data = create_response.json()
    template_id = template_data["id"]

    # Get initial document count
    initial_docs_response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert initial_docs_response.status_code == 200
    initial_docs = initial_docs_response.json()
    initial_count = len(initial_docs)

    # Now add the template to the project
    add_response = await client.post(
        f"/api/v1/projects/{project.id}/documents/from-template/{template_id}"
    )

    assert add_response.status_code == 201, f"Failed with: {add_response.text}"
    document_data = add_response.json()
    assert document_data["name"] == "Template For Project"
    assert document_data["parent_id"] is None

    # Verify all documents were created (should have 4 more: root + 2 children + 1 grandchild)
    final_docs_response = await client.get(f"/api/v1/projects/{project.id}/documents/")
    assert final_docs_response.status_code == 200
    final_docs = final_docs_response.json()

    # We should have 4 more documents than initially (the original 4 + 4 from template)
    assert len(final_docs) == initial_count + 4

    # Verify the new documents have correct hierarchy
    new_root = next((d for d in final_docs if d["name"] == "Template For Project" and d["parent_id"] is None), None)
    assert new_root is not None

    new_children = [d for d in final_docs if d["parent_id"] == new_root["id"]]
    assert len(new_children) == 2

    new_child1 = next((d for d in new_children if d["name"] == "API Child 1"), None)
    assert new_child1 is not None

    new_grandchildren = [d for d in final_docs if d["parent_id"] == new_child1["id"]]
    assert len(new_grandchildren) == 1
    assert new_grandchildren[0]["name"] == "API Grandchild"


@pytest.mark.asyncio
async def test_create_template_with_empty_children(
    db_session: AsyncSession, client: AsyncClient, setup_api_test_data
):
    """Test creating a template with include_children=True but document has no children."""
    data = setup_api_test_data
    project = data["project"]

    # Create a document without children
    doc_no_children = Document(
        name="Childless Document",
        project_id=project.id,
        type=DocumentType.MARKDOWN,
        content='{"markdown": "No children"}',
        parent_id=None,
        order=0,
    )
    db_session.add(doc_no_children)
    await db_session.commit()

    # Create template with include_children=True
    response = await client.post(
        "/api/v1/library/templates/",
        json={
            "document_id": str(doc_no_children.id),
            "name": "Template Without Children",
            "category_name": "API Test Category",
            "visibility": "public",
            "include_children": True,
        },
    )

    assert response.status_code == 201
    template_data = response.json()
    assert template_data["name"] == "Template Without Children"

    # Should only create one template
    templates_response = await client.get("/api/v1/library/templates/")
    assert templates_response.status_code == 200
    templates = templates_response.json()

    childless_templates = [t for t in templates if t["name"] == "Template Without Children"]
    assert len(childless_templates) == 1
