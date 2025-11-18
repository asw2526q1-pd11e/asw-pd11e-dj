# flake8: noqa E501
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post, Comment
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# -------------------- SERIALIZERS --------------------


class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(help_text="Títol del post, màxim 200 caràcters")
    content = serializers.CharField(help_text="Contingut complet del post")
    author = serializers.CharField(source="author.username", help_text="Nom d'usuari de l'autor")
    published_date = serializers.DateTimeField(help_text="Data de publicació")
    votes = serializers.IntegerField(help_text="Número de vots del post")
    url = serializers.CharField(help_text="URL absoluta del post")

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'published_date', 'votes', 'url']


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", help_text="Nom d'usuari de l'autor del comentari")
    image = serializers.ImageField(help_text="URL de la imatge del comentari, si existeix")

    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'content', 'author', 'published_date', 'votes', 'url', 'image']


class CommentTreeSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username")
    image = serializers.ImageField(allow_null=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'published_date', 'votes', 'image', 'replies']

    def get_replies(self, obj):
        children = obj.replies.all().order_by('published_date')
        serializer = CommentTreeSerializer(children, many=True)
        return serializer.data


# -------------------- RESPONSES --------------------

responses_200 = {200: 'OK'}
responses_post_detail = {
    200: PostSerializer,
    404: 'Not Found - post no trobat',
}
responses_post_comments = {
    200: CommentSerializer(many=True),
    404: 'Not Found - post no trobat',
}
responses_post_comments_tree = {
    200: CommentTreeSerializer(many=True),
    404: 'Not Found - post no trobat',
}
responses_post_comments_root = {
    200: CommentTreeSerializer(many=True),
    404: 'Not Found - post no trobat',
}
responses_search = {
    200: 'Posts i/o comentaris trobats',
    400: 'Bad Request - cal paràmetre q',
}


# -------------------- VISTES --------------------

# Llista de tots els posts
@swagger_auto_schema(
    method='get',
    operation_description="Retorna la llista de tots els posts",
    responses=responses_200
)
@api_view(['GET'])
def post_list(request):
    posts = Post.objects.all()
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


# Detall d'un post concret
@swagger_auto_schema(
    method='get',
    operation_description="Retorna un post concret amb totes les seves dades. Retorna 404 si no existeix.",
    responses=responses_post_detail
)
@api_view(['GET'])
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    serializer = PostSerializer(post)
    return Response(serializer.data)


# Tots els comentaris d'un post
@swagger_auto_schema(
    method='get',
    operation_description="Retorna tots els comentaris d'un post concret.",
    responses=responses_post_comments
)
@api_view(['GET'])
def post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = Comment.objects.filter(post=post).order_by('published_date')
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


# Comentaris en arbre
@swagger_auto_schema(
    method='get',
    operation_description="Retorna els comentaris d'un post amb l'estructura en arbre (fills dins de replies).",
    responses=responses_post_comments_tree
)
@api_view(['GET'])
def post_comments_tree(request, pk):
    post = get_object_or_404(Post, pk=pk)
    root_comments = Comment.objects.filter(post=post, parent__isnull=True).order_by('published_date')
    serializer = CommentTreeSerializer(root_comments, many=True)
    return Response(serializer.data)


# Comentaris només de primer nivell
@swagger_auto_schema(
    method='get',
    operation_description="Retorna només els comentaris de primer nivell d'un post.",
    responses=responses_post_comments_root
)
@api_view(['GET'])
def post_comments_root(request, pk):
    post = get_object_or_404(Post, pk=pk)
    root_comments = Comment.objects.filter(post=post, parent__isnull=True).order_by('published_date')
    serializer = CommentTreeSerializer(root_comments, many=True)
    for c in serializer.data:
        c['replies'] = []
    return Response(serializer.data)


# Cerca posts i comentaris
query_param = openapi.Parameter(
    'q', openapi.IN_QUERY,
    description="Text a cercar",
    type=openapi.TYPE_STRING,
    required=True
)
type_param = openapi.Parameter(
    'type', openapi.IN_QUERY,
    description="Tipus de cerca: posts | comments | both (per defecte: both)",
    type=openapi.TYPE_STRING,
    required=False,
    default='both'
)

@swagger_auto_schema(
    method='get',
    manual_parameters=[query_param, type_param],
    operation_description="Cerca posts i/o comentaris pel text indicat.",
    responses=responses_search
)
@api_view(['GET'])
def search_posts_comments(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'both').lower()

    if not query:
        return Response({"error": "Cal especificar el paràmetre q"}, status=400)

    result = {}
    if search_type in ['posts', 'both']:
        posts = Post.objects.filter(title__icontains=query).order_by('-published_date')
        result['posts'] = PostSerializer(posts, many=True).data
    if search_type in ['comments', 'both']:
        comments = Comment.objects.filter(content__icontains=query).order_by('-published_date')
        result['comments'] = CommentSerializer(comments, many=True).data

    return Response({"query": query, "type": search_type, **result})
