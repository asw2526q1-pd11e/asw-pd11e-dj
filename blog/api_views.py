from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from .models import Comment


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


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(
        source="author.username",
        help_text="Nom d'usuari de l'autor del comentari"
        )
    image = serializers.ImageField(
        help_text="URL de la imatge del comentari, si existeix"
        )

    class Meta:
        model = Comment
        fields = [
            'id',
            'post',
            'parent',
            'content',
            'author',
            'published_date',
            'votes',
            'url',
            'image'
        ]


class CommentTreeSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")
    image = serializers.ImageField(allow_null=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'author',
            'published_date',
            'votes',
            'image',
            'replies'
        ]

    def get_replies(self, obj):
        children = obj.replies.all().order_by('published_date')
        serializer = CommentTreeSerializer(children, many=True)
        return serializer.data
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


@swagger_auto_schema(
    method='get',
    operation_description="Retorna tots els comentaris d'un post concret. Cada comentari inclou autor, contingut, data, vots i URL de la imatge si existeix.", # noqa E501
    responses={200: CommentSerializer(many=True), 404: 'Not found'}
)
@api_view(['GET'])
def post_comments(request, pk):
    """
    GET /posts/{id}/comments/
    Retorna tots els comentaris del post amb id=pk.
    """
    post = get_object_or_404(Post, pk=pk)
    comments = Comment.objects.filter(post=post).order_by('published_date')
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna els comentaris d'un post amb l'estructura en arbre (fills dins de replies).", # noqa E501
    responses={200: CommentTreeSerializer(many=True), 404: 'Not found'}
)
@api_view(['GET'])
def post_comments_tree(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # només els comentaris arrel
    root_comments = Comment.objects.filter(
        post=post,
        parent__isnull=True
    ).order_by('published_date')
    serializer = CommentTreeSerializer(root_comments, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna només els comentaris de primer nivell d'un post.", # noqa E501
    responses={200: CommentTreeSerializer(many=True), 404: 'Not found'}
)
@api_view(['GET'])
def post_comments_root(request, pk):
    post = get_object_or_404(Post, pk=pk)
    root_comments = Comment.objects.filter(
        post=post,
        parent__isnull=True
        ).order_by('published_date')
    serializer = CommentTreeSerializer(root_comments, many=True)
    # buidem replies 1r nivell
    for c in serializer.data:
        c['replies'] = []
    return Response(serializer.data)
