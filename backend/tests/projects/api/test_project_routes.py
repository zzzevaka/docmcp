"""Test project routes."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.projects.models import Project
from app.users.models import Team, TeamMember, TeamRole, User


@pytest.mark.asyncio
async def test_list_projects(db_session: AsyncSession, client: AsyncClient):
    """Test listing projects for user's teams."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="List Projects Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.flush()

    project1 = Project(name="Project 1", team_id=team.id)
    project2 = Project(name="Project 2", team_id=team.id)
    db_session.add(project1)
    db_session.add(project2)
    await db_session.commit()

    response = await client.get("/api/v1/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) >= 2
    project_names = [p["name"] for p in projects]
    assert "Project 1" in project_names
    assert "Project 2" in project_names


@pytest.mark.asyncio
async def test_list_projects_empty(db_session: AsyncSession, client: AsyncClient):
    """Test listing projects when user has no teams."""
    response = await client.get("/api/v1/projects/")
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)


@pytest.mark.asyncio
async def test_get_project(db_session: AsyncSession, client: AsyncClient):
    """Test getting a project by ID."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Get Project Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.flush()

    project = Project(name="Test Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["id"] == str(project.id)


@pytest.mark.asyncio
async def test_get_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test getting non-existent project."""
    fake_id = uuid4()
    response = await client.get(f"/api/v1/projects/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test getting project when user is not team member."""
    team = Team(name="Other Project Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    response = await client.get(f"/api/v1/projects/{project.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_project(db_session: AsyncSession, client: AsyncClient):
    """Test creating a new project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Create Project Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.commit()

    payload = {
        "name": "New Project",
        "team_id": str(team.id),
    }

    response = await client.post("/api/v1/projects/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert data["team_id"] == str(team.id)


@pytest.mark.asyncio
async def test_create_project_team_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test creating project with non-existent team."""
    fake_team_id = uuid4()
    payload = {
        "name": "New Project",
        "team_id": str(fake_team_id),
    }

    response = await client.post("/api/v1/projects/", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_project_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test creating project when user is not team member."""
    team = Team(name="Other Create Team")
    db_session.add(team)
    await db_session.commit()

    payload = {
        "name": "New Project",
        "team_id": str(team.id),
    }

    response = await client.post("/api/v1/projects/", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_project(db_session: AsyncSession, client: AsyncClient):
    """Test updating a project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Update Project Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.flush()

    project = Project(name="Original Name", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    payload = {"name": "Updated Name"}

    response = await client.put(f"/api/v1/projects/{project.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test updating non-existent project."""
    fake_id = uuid4()
    payload = {"name": "Updated Name"}

    response = await client.put(f"/api/v1/projects/{fake_id}", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test updating project when user is not team member."""
    team = Team(name="Other Update Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    payload = {"name": "Updated Name"}

    response = await client.put(f"/api/v1/projects/{project.id}", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_project(db_session: AsyncSession, client: AsyncClient):
    """Test deleting a project."""
    result = await db_session.execute(select(User).where(User.username == "testuser"))
    user = result.scalar_one()

    team = Team(name="Delete Project Team")
    db_session.add(team)
    await db_session.flush()

    # Add user to team
    team_member = TeamMember(user_id=user.id, team_id=team.id, role=TeamRole.MEMBER)
    db_session.add(team_member)
    await db_session.flush()

    project = Project(name="To Delete", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    response = await client.delete(f"/api/v1/projects/{project.id}")
    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/projects/{project.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found(db_session: AsyncSession, client: AsyncClient):
    """Test deleting non-existent project."""
    fake_id = uuid4()
    response = await client.delete(f"/api/v1/projects/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_team_member(db_session: AsyncSession, client: AsyncClient):
    """Test deleting project when user is not team member."""
    team = Team(name="Other Delete Team")
    db_session.add(team)
    await db_session.flush()

    project = Project(name="Other Project", team_id=team.id)
    db_session.add(project)
    await db_session.commit()

    response = await client.delete(f"/api/v1/projects/{project.id}")
    assert response.status_code == 403
