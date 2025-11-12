import pytest
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from blog.models import Post
from communities.models import Community


@pytest.mark.django_db
def test_post_create_view(client):
    # Crear usuario y loguearlo
    user = User.objects.create_user(username="nuevoautor", password="testpass")
    client.login(username="nuevoautor", password="testpass")

    # Crear comunidad
    community = Community.objects.create(name="Test Community")

    url = reverse("blog:post_create")
    data = {
        "title": "Nuevo Post",
        "content": "Contenido del nuevo post",
        "published_date": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": "",
        "communities": [community.id],  # ManyToMany
    }

    # Enviar POST para crear el post
    response = client.post(url, data)

    # Redirige correctamente al listado
    assert response.status_code == 302
    assert response.url == reverse("blog:post_list")

    # El post se ha creado correctamente
    post = Post.objects.get(title="Nuevo Post")
    assert post.content == "Contenido del nuevo post"
    assert post.author == user  # usuario autenticado
    assert community in post.communities.all()  # ✅ ahora pasa
    assert post.url == post.get_absolute_url()
