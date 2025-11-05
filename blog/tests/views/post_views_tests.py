import pytest
from django.urls import reverse
from django.utils import timezone
from blog.models.post import Post
from communities.models import Community


@pytest.mark.django_db
def test_post_list_view(client):
    Post.objects.create(
        title="Post 1",
        content="Contenido 1",
        author="Autor 1",
        published_date=timezone.now(),
    )
    Post.objects.create(
        title="Post 2",
        content="Contenido 2",
        author="Autor 2",
        published_date=timezone.now(),
    )

    url = reverse("blog:post_list")
    response = client.get(url)

    assert response.status_code == 200

    content = response.content.decode()
    assert "Post 1" in content
    assert "Post 2" in content


@pytest.mark.django_db
def test_post_create_view(client):
    community = Community.objects.create(name="Test Community")

    url = reverse("blog:post_create")
    data = {
        "title": "Nuevo Post",
        "content": "Contenido del nuevo post",
        "author": "Nuevo Autor",
        "published_date": timezone.now(),
        "url": "",
        "communities": [community.id],
    }

    response = client.post(url, data)

    assert response.status_code == 302
    assert response.url == reverse("blog:post_list")

    post = Post.objects.get(title="Nuevo Post")
    assert post is not None
    assert post.content == "Contenido del nuevo post"
    assert post.author == "Nuevo Autor"

    assert community in post.communities.all()

    assert post.url == post.get_absolute_url()
