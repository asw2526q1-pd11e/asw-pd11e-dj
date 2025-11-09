import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from blog.models.comment import Comment
from blog.models.post import Post


@pytest.mark.django_db
def test_create_comment_with_post():
    """Debe crear un comentario asociado a un post correctamente."""
    post = Post.objects.create(
        title="Test Post", content="Post content", author="Post Author"
    )

    comment = Comment.objects.create(
        post=post,
        content="This is a test comment.",
        author="Test Author",
        votes=5,
    )

    assert comment.id is not None
    assert comment.content == "This is a test comment."
    assert comment.author == "Test Author"
    assert comment.votes == 5
    assert comment.url == post.url  # hereda la url del post
    assert comment.post == post
    assert isinstance(comment.published_date, timezone.datetime)


# ---------- FIELD VALIDATIONS ---------- #


@pytest.mark.django_db
def test_comment_requires_post():
    """Debe lanzar error si se crea sin post."""
    with pytest.raises(IntegrityError):
        Comment.objects.create(content="No post", author="Anon")


@pytest.mark.django_db
def test_content_cannot_be_null():
    """El campo content no puede ser NULL."""
    post = Post.objects.create(
        title="Test Post", content="Post content", author="Post Author"
    )
    with pytest.raises(IntegrityError):
        Comment.objects.create(post=post, content=None, author="Author")


@pytest.mark.django_db
def test_content_cannot_be_blank():
    """El campo content vacío debe fallar en validación."""
    post = Post.objects.create(
        title="Test Post", content="Post content", author="Post Author"
    )
    comment = Comment(post=post, content="", author="Author")
    with pytest.raises(ValidationError):
        comment.full_clean()


def test_content_max_length():
    """Debe tener max_length = 5000"""
    max_length = Comment._meta.get_field("content").max_length
    assert max_length == 5000


# ---------- AUTHOR FIELD ---------- #


@pytest.mark.django_db
def test_author_cannot_be_null():
    post = Post.objects.create(
        title="Test Post", content="Post content", author="Post Author"
    )
    with pytest.raises(IntegrityError):
        Comment.objects.create(post=post, content="Content", author=None)


@pytest.mark.django_db
def test_author_cannot_be_blank():
    post = Post.objects.create(
        title="Test Post", content="Post content", author="Post Author"
    )
    comment = Comment(post=post, content="Content", author="")
    with pytest.raises(ValidationError):
        comment.full_clean()


def test_author_max_length():
    max_length = Comment._meta.get_field("author").max_length
    assert max_length == 100


# ---------- PUBLISHED DATE ---------- #


def test_published_date_default():
    field = Comment._meta.get_field("published_date")
    assert field.default == timezone.now


# ---------- VOTES ---------- #


def test_votes_default_value():
    field = Comment._meta.get_field("votes")
    assert field.default == 0


# ---------- IMAGE ---------- #


def test_image_field_allows_blank_and_null():
    field = Comment._meta.get_field("image")
    assert field.blank is True
    assert field.null is True


# ---------- URL ---------- #


def test_url_field_allows_blank_and_null():
    field = Comment._meta.get_field("url")
    assert field.blank is True
    assert field.null is True


@pytest.mark.django_db
def test_url_defaults_to_post_url():
    """Si no se pasa URL, debe copiar la del post."""
    post = Post.objects.create(
        title="Post con URL",
        content="Contenido",
        author="Autor",
        url="https://example.com/post",
    )
    comment = Comment.objects.create(
        post=post, content="Comentario vinculado", author="Autor C"
    )
    assert comment.url == "https://example.com/post"


@pytest.mark.django_db
def test_comment_str_representation():
    """El __str__ debe incluir el autor y parte del contenido."""
    post = Post.objects.create(
        title="Post Title", content="Some post content", author="Author"
    )
    comment = Comment.objects.create(
        post=post, content="This is a test comment content.", author="Tester"
    )
    result = str(comment)
    assert "Tester" in result
    assert "Comment" in result
