import pytest
from django.urls import reverse
from rest_framework import status
from community.models import SkillCategory, Skill

pytestmark = pytest.mark.django_db

# --- FIXTURES ---


@pytest.fixture
def category_payload():
    return {"name": "Backend Tech", "color_theme": "blue"}


@pytest.fixture
def skill_payload():
    return {"name": "Django", "proficiency": "expert", "icon_name": "django"}


# --- TESTS ---


def test_create_category(api_client_factory, user_factory, category_payload):
    # Setup User & Client
    user = user_factory()
    client = api_client_factory(user=user)

    # CORRECTED URL: Added 'community:' prefix
    url = reverse("community:profile-skill-categories-list")
    response = client.post(url, category_payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert SkillCategory.objects.count() == 1
    category = SkillCategory.objects.first()
    assert category.user_profile == user.profile
    assert category.name == "Backend Tech"


def test_create_skill_in_category(api_client_factory, user_factory, skill_payload):
    # Setup User & Client
    user = user_factory()
    client = api_client_factory(user=user)

    # 1. Create Category directly
    category = SkillCategory.objects.create(user_profile=user.profile, name="Frontend")

    # 2. Create Skill (Must provide category ID)
    # CORRECTED URL: Added 'community:' prefix
    url = reverse("community:profile-skills-list")
    skill_payload["category"] = category.id

    response = client.post(url, skill_payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert Skill.objects.count() == 1
    skill = Skill.objects.first()
    assert skill.category == category
    assert skill.proficiency == "expert"


def test_cannot_add_skill_to_others_category(
    api_client_factory, user_factory, skill_payload
):
    # User A (Attacker)
    attacker = user_factory(username="attacker")
    client = api_client_factory(user=attacker)

    # User B (Victim) creates a category
    victim = user_factory(username="victim")
    victim_category = SkillCategory.objects.create(
        user_profile=victim.profile, name="Secret Tech"
    )

    # Attacker tries to add a skill to Victim's category
    # CORRECTED URL: Added 'community:' prefix
    url = reverse("community:profile-skills-list")
    skill_payload["category"] = victim_category.id

    response = client.post(url, skill_payload)

    # Should fail (400 Bad Request - Validation Error)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "category" in response.data


def test_list_skills_returns_nested_structure(api_client_factory, user_factory):
    # Setup User & Client
    user = user_factory()
    client = api_client_factory(user=user)

    # Setup Data directly in DB
    cat = SkillCategory.objects.create(user_profile=user.profile, name="DevOps")
    Skill.objects.create(category=cat, name="Docker", proficiency="intermediate")

    # Hit Profile Endpoint
    url = reverse("community:userprofile-detail", kwargs={"username": user.username})
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.data

    # Verify structure matches Serializer
    assert "skill_categories" in data
    assert len(data["skill_categories"]) == 1
    assert data["skill_categories"][0]["name"] == "DevOps"

    # Verify nested skills
    skills = data["skill_categories"][0]["skills"]
    assert len(skills) == 1
    assert skills[0]["name"] == "Docker"
