import pytest
from communities.models import Community


@pytest.mark.django_db
def test_create_community():
    community = Community.objects.create(
        name="Test Community",
    )
    assert community.id is not None
    assert community.name == "Test Community"
    assert not community.avatar
    assert not community.banner


# Testing Name Field
@pytest.mark.django_db
def test_name_can_be_null():
    community = Community.objects.create(name=None)
    assert community.id is not None
    assert community.name is None


@pytest.mark.django_db
def test_name_can_be_blank():
    community = Community.objects.create(name="")
    assert community.id is not None
    assert community.name == ""


def test_name_max_length():
    max_length = Community._meta.get_field("name").max_length
    assert max_length == 200


# Testing Avatar Field
@pytest.mark.django_db
def test_avatar_can_be_null():
    community = Community.objects.create(
        name="Test Community",
        avatar=None
    )
    assert community.id is not None
    assert not community.avatar


@pytest.mark.django_db
def test_avatar_can_be_blank():
    community = Community.objects.create(
        name="Test Community",
        avatar=""
    )
    assert community.id is not None
    assert community.avatar.name == ""


def test_avatar_field_is_imagefield():
    avatar_field = Community._meta.get_field("avatar")
    assert avatar_field.__class__.__name__ == "ImageField"


# Testing Banner Field
@pytest.mark.django_db
def test_banner_can_be_null():
    community = Community.objects.create(
        name="Test Community",
        banner=None
    )
    assert community.id is not None
    assert not community.banner


@pytest.mark.django_db
def test_banner_can_be_blank():
    community = Community.objects.create(
        name="Test Community",
        banner=""
    )
    assert community.id is not None
    assert community.banner.name == ""


def test_banner_field_is_imagefield():
    banner_field = Community._meta.get_field("banner")
    assert banner_field.__class__.__name__ == "ImageField"


# Testing __str__ method
@pytest.mark.django_db
def test_str_with_name():
    community = Community.objects.create(name="My Community")
    assert str(community) == "My Community"


@pytest.mark.django_db
def test_str_without_name():
    community = Community.objects.create(name=None)
    assert str(community) == f"Comunitat #{community.id}"


@pytest.mark.django_db
def test_str_with_empty_name():
    community = Community.objects.create(name="")
    assert str(community) == f"Comunitat #{community.id}"


# Testing ID Field
def test_id_is_primary_key():
    id_field = Community._meta.get_field("id")
    assert id_field.primary_key is True


def test_id_is_bigautofield():
    id_field = Community._meta.get_field("id")
    assert id_field.__class__.__name__ == "BigAutoField"
