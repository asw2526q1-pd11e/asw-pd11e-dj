import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from blog.models.post import Post


@pytest.mark.django_db
def test_create_post():
    post = Post.objects.create(
        title="Test Post",
        content="This is a test post content.",
        author="Test Author",
        published_date=timezone.now(),
        votes=5,
        url="https://example.com",
    )
    assert post.id is not None
    assert post.title == "Test Post"
    assert post.content == "This is a test post content."
    assert post.author == "Test Author"
    assert post.votes == 5
    assert post.url == "https://example.com"
    assert isinstance(post.published_date, timezone.datetime)


# Title Field
@pytest.mark.django_db
def test_title_cannot_be_null():
    with pytest.raises(IntegrityError):
        Post.objects.create(
            title=None, content="Content without a title.", author="Author"
        )


@pytest.mark.django_db
def test_title_cannot_be_blank():
    post = Post(title="", content="Content with blank title.", author="Author")
    with pytest.raises(ValidationError):
        post.full_clean()


def test_title_max_length():
    max_length = Post._meta.get_field("title").max_length
    assert max_length == 200


# Content Field
@pytest.mark.django_db
def test_content_cannot_be_null():
    with pytest.raises(IntegrityError):
        Post.objects.create(title="Title", content=None, author="Author")


@pytest.mark.django_db
def test_content_cannot_be_blank():
    post = Post(title="Title", content="", author="Author")
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


@pytest.mark.django_db
def test_author_cannot_be_blank():
    post = Post(title="Title", content="Content", author="")
    with pytest.raises(ValidationError):
        post.full_clean()


def test_author_max_length():
    max_length = Post._meta.get_field("author").max_length
    assert max_length == 100


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
    post = Post(
        title="Title",
        content="Content",
        author="Author",
        url="not-a-valid-url"
    )
    with pytest.raises(ValidationError):
        post.full_clean()
