import pytest
from blog.models.post import Post
from django.utils import timezone


@pytest.mark.django_db
def test_create_post():
    post = Post.objects.create(
        title="Test Post",
        content="This is a test post content.",
        author="Test Author",
        published_date=timezone.now(),
    )
    assert post.id is not None
    assert post.title == "Test Post"
    assert post.content == "This is a test post content."
    assert post.author == "Test Author"


# Testing Title Field
@pytest.mark.django_db
def test_post_name_cannot_be_null():
    with pytest.raises(Exception):
        Post.objects.create(
            title=None,
            content="Content without a title.",
            author="Author",
            published_date=timezone.now(),
        )


@pytest.mark.django_db
def test_name_cannot_be_blank():
    post = Post(
        title="",
        content="Content with blank title.",
        author="Author",
        published_date=timezone.now(),
    )
    with pytest.raises(Exception):
        post.full_clean()
        post.save()


def test_name_max_length():
    max_length = Post._meta.get_field("title").max_length
    assert max_length == 200


# Testing Content Field
@pytest.mark.django_db
def test_content_cannot_be_null():
    with pytest.raises(Exception):
        Post.objects.create(
            title="Title",
            content=None,
            author="Author",
            published_date=timezone.now(),
        )


@pytest.mark.django_db
def test_content_cannot_be_blank():
    post = Post(
        title="Title",
        content="",
        author="Author",
        published_date=timezone.now(),
    )
    with pytest.raises(Exception):
        post.full_clean()
        post.save()


def test_content_max_length():
    max_length = Post._meta.get_field("content").max_length
    assert max_length == 5000


# Testing Author Field
@pytest.mark.django_db
def test_author_cannot_be_null():
    with pytest.raises(Exception):
        Post.objects.create(
            title="Title",
            content="Content",
            author=None,
            published_date=timezone.now(),
        )


@pytest.mark.django_db
def test_author_cannot_be_blank():
    post = Post(
        title="Title",
        content="Content",
        author="",
        published_date=timezone.now(),
    )
    with pytest.raises(Exception):
        post.full_clean()
        post.save()


def test_author_max_length():
    max_length = Post._meta.get_field("author").max_length
    assert max_length == 100


# Testing Published Date Field
def test_published_date_default():
    published_date_field = Post._meta.get_field("published_date")
    assert published_date_field.default == timezone.now
