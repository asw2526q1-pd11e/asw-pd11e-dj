import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django.contrib.auth.models import User
from blog.models.comment import Comment
from blog.models.post import Post


@pytest.mark.django_db
def test_create_comment_with_post():
    """Debe crear un comentario asociado a un post correctamente."""
    user_post = User.objects.create_user(
        username="post_author", password="1234"
    )
    user_comment = User.objects.create_user(
        username="comment_author", password="1234"
    )

    post = Post.objects.create(
        title="Test Post",
        content="Post content",
        author=user_post,
    )

    comment = Comment.objects.create(
        post=post,
        content="This is a test comment.",
        author=user_comment,
        votes=5,
    )

    assert comment.id is not None
    assert comment.content == "This is a test comment."
    assert comment.author == user_comment
    assert comment.votes == 5
    assert comment.url == post.url  # hereda la url del post
    assert comment.post == post
    assert isinstance(comment.published_date, timezone.datetime)


# ---------- FIELD VALIDATIONS ---------- #

@pytest.mark.django_db
def test_comment_requires_post():
    """Debe lanzar error si se crea sin post."""
    user = User.objects.create_user(username="testuser", password="1234")
    with pytest.raises(IntegrityError):
        Comment.objects.create(content="No post", author=user)


@pytest.mark.django_db
def test_content_cannot_be_null():
    """El campo content no puede ser NULL."""
    user_post = User.objects.create_user(
        username="post_author", password="1234"
    )
    user_comment = User.objects.create_user(
        username="comment_author", password="1234"
    )
    post = Post.objects.create(
        title="Test Post",
        content="Post content",
        author=user_post,
    )
    with pytest.raises(IntegrityError):
        Comment.objects.create(post=post, content=None, author=user_comment)


@pytest.mark.django_db
def test_content_cannot_be_blank():
    """El campo content vacío debe fallar en validación."""
    user_post = User.objects.create_user(
        username="post_author", password="1234"
    )
    user_comment = User.objects.create_user(
        username="comment_author", password="1234"
    )
    post = Post.objects.create(
        title="Test Post",
        content="Post content",
        author=user_post,
    )
    comment = Comment(post=post, content="", author=user_comment)
    with pytest.raises(ValidationError):
        comment.full_clean()


def test_content_max_length():
    """Debe tener max_length = 5000"""
    max_length = Comment._meta.get_field("content").max_length
    assert max_length == 5000


# ---------- AUTHOR FIELD ---------- #

@pytest.mark.django_db
def test_author_cannot_be_null():
    user_post = User.objects.create_user(
        username="post_author", password="1234"
    )
    post = Post.objects.create(
        title="Test Post",
        content="Post content",
        author=user_post,
    )
    with pytest.raises(IntegrityError):
        Comment.objects.create(post=post, content="Content", author=None)


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
    user_post = User.objects.create_user(username="post_author",
                                         password="1234")
    user_comment = User.objects.create_user(
        username="comment_author", password="1234"
    )
    post = Post.objects.create(
        title="Post con URL",
        content="Contenido",
        author=user_post,
        url="https://example.com/post",
    )
    comment = Comment.objects.create(post=post, content="Comentario vinculado",
                                     author=user_comment)
    assert comment.url == "https://example.com/post"


@pytest.mark.django_db
def test_comment_str_representation():
    user_post = User.objects.create_user(username="post_author",
                                         password="1234")
    user_comment = User.objects.create_user(
        username="comment_author", password="1234"
    )
    post = Post.objects.create(
        title="Post Title",
        content="Some post content",
        author=user_post,
    )
    comment = Comment.objects.create(
        post=post,
        content="This is a test comment content.",
        author=user_comment,
    )
    result = str(comment)
    assert "comment_author" in result  # ahora el username del User
    assert "Comment" in result
