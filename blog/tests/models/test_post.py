import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from blog.models.post import Post


@pytest.mark.django_db
def test_create_post():
    user = User.objects.create_user(username="testuser", password="1234")
    post = Post.objects.create(
        title="Test Post",
        content="This is a test post content.",
        author=user,
        published_date=timezone.now(),
        votes=5,
        url="https://example.com",
    )
    assert post.id is not None
    assert post.title == "Test Post"
    assert post.content == "This is a test post content."
    assert post.author == user
    assert post.votes == 5
    assert post.url == "https://example.com"
    assert isinstance(post.published_date, timezone.datetime)


# Title Field
@pytest.mark.django_db
def test_title_cannot_be_null():
    user = User.objects.create_user(username="testuser", password="1234")
    with pytest.raises(IntegrityError):
        Post.objects.create(title=None, content="Content", author=user)


@pytest.mark.django_db
def test_title_cannot_be_blank():
    user = User.objects.create_user(username="testuser", password="1234")
    post = Post(title="", content="Content", author=user)
    with pytest.raises(ValidationError):
        post.full_clean()


def test_title_max_length():
    max_length = Post._meta.get_field("title").max_length
    assert max_length == 200


# Content Field
@pytest.mark.django_db
def test_content_cannot_be_null():
    user = User.objects.create_user(username="testuser", password="1234")
    with pytest.raises(IntegrityError):
        Post.objects.create(title="Title", content=None, author=user)


@pytest.mark.django_db
def test_content_cannot_be_blank():
    user = User.objects.create_user(username="testuser", password="1234")
    post = Post(title="Title", content="", author=user)
    with pytest.raises(ValidationError):
        post.full_clean()


def test_content_max_length():
    max_length = Post._meta.get_field("content").max_length
    assert max_length == 5000


# Author Field
@pytest.mark.django_db
def test_author_cannot_be_null():
    with pytest.raises(IntegrityError):
        Post.objects.create(title="Title", content="Content", author=None)


# Nota: no hay 'blank' ni 'max_length' en ForeignKey
# Por eso se eliminan los tests que usaban 'blank' o 'max_length' en author


# Published Date Field
def test_published_date_default():
    published_date_field = Post._meta.get_field("published_date")
    assert published_date_field.default == timezone.now


# Votes Field
def test_votes_default_value():
    field = Post._meta.get_field("votes")
    assert field.default == 0


# Image Field
def test_image_field_allows_blank_and_null():
    field = Post._meta.get_field("image")
    assert field.blank is True
    assert field.null is True


# URL Field
def test_url_field_allows_blank_and_null():
    field = Post._meta.get_field("url")
    assert field.blank is True
    assert field.null is True


@pytest.mark.django_db
def test_invalid_url_raises_validation_error():
    user = User.objects.create_user(username="testuser", password="1234")
    post = Post(
        title="Title",
        content="Content",
        author=user,
        url="not-a-valid-url"
    )
    with pytest.raises(ValidationError):
        post.full_clean()
