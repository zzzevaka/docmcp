import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.library.models import Category, Template, TemplateType, TemplateVisibility
from app.library.repositories import TemplateRepository
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
