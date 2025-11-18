from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema

# -------------------- SERIALIZER --------------------


class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        help_text="Títol del post, màxim 200 caràcters"
        )
    content = serializers.CharField(help_text="Contingut complet del post")
    author = serializers.CharField(
        source="author.username",
        help_text="Nom d'usuari de l'autor"
        )
    published_date = serializers.DateTimeField(help_text="Data de publicació")
    votes = serializers.IntegerField(help_text="Número de vots del post")
    url = serializers.CharField(help_text="URL absoluta del post")

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'author',
            'published_date',
            'votes',
            'url'
        ]

# -------------------- VISTES --------------------


@swagger_auto_schema(
    method='get',
    operation_description="Retorna la llista de tots els posts",
    responses={200: PostSerializer(many=True)}
)
@api_view(['GET'])
def post_list(request):
    posts = Post.objects.all()
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna un post concret amb totes les seves dades. Retorna 404 si no existeix.", # noqa E501
    responses={200: PostSerializer, 404: 'Not found'}
)
@api_view(['GET'])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    serializer = PostSerializer(post)
    return Response(serializer.data)
