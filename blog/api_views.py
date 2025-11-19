# flake8: noqa E501
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post, Comment
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from communities.api_views import CommunitySerializer

# -------------------- SERIALIZERS --------------------


class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(help_text="Títol del post, màxim 200 caràcters")
    content = serializers.CharField(help_text="Contingut complet del post")
    author = serializers.CharField(source="author.username", help_text="Nom d'usuari de l'autor")
    published_date = serializers.DateTimeField(help_text="Data de publicació")
    votes = serializers.IntegerField(help_text="Número de vots del post")
    url = serializers.CharField(help_text="URL absoluta del post")
    communities = CommunitySerializer(
        many=True,
        read_only=True,
        help_text="Llista de comunitats a les quals pertany el post"
    )

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'published_date', 'votes', 'url', 'communities']
        ref_name = "PostSerializerWithCommunities"


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", help_text="Nom d'usuari de l'autor del comentari")
    image = serializers.ImageField(help_text="URL de la imatge del comentari, si existeix", allow_null=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'content', 'author', 'published_date', 'votes', 'url', 'image']


class CommentTreeSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", help_text="Nom d'usuari de l'autor del comentari")
    image = serializers.ImageField(allow_null=True, help_text="URL de la imatge del comentari, si existeix")
    replies = serializers.SerializerMethodField(help_text="Llista de respostes (comentaris fills) en estructura recursiva")

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'published_date', 'votes', 'image', 'replies']

    def get_replies(self, obj):
        children = obj.replies.all().order_by('published_date')
        serializer = CommentTreeSerializer(children, many=True)
        return serializer.data


# -------------------- VISTES --------------------

@swagger_auto_schema(
    method='get',
    operation_description="Retorna la llista de tots els posts amb les seves comunitats",
    responses={
        200: PostSerializer(many=True),
        500: 'Error intern del servidor'
    }
)
@api_view(['GET'])
def post_list(request):
    """
    GET /api/posts/
    Retorna tots els posts amb informació de les comunitats a les quals pertanyen.
    """
    posts = Post.objects.prefetch_related('communities').all()
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna un post concret amb totes les seves dades i comunitats",
    responses={
        200: PostSerializer,
        404: 'Not Found - post no trobat'
    }
)
@api_view(['GET'])
def post_detail(request, pk):
    """
    GET /api/posts/{id}/
    Retorna la informació detallada d'un post concret.
    """
    post = get_object_or_404(Post.objects.prefetch_related('communities'), pk=pk)
    serializer = PostSerializer(post)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna tots els comentaris d'un post concret ordenats per data de publicació",
    responses={
        200: CommentSerializer(many=True),
        404: 'Not Found - post no trobat'
    }
)
@api_view(['GET'])
def post_comments(request, pk):
    """
    GET /api/posts/{id}/comments/
    Retorna tots els comentaris (plana sense jerarquia) d'un post.
    """
    post = get_object_or_404(Post, pk=pk)
    comments = Comment.objects.filter(post=post).order_by('published_date')
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna els comentaris d'un post amb estructura jeràrquica en arbre (fills dins de 'replies')",
    responses={
        200: CommentTreeSerializer(many=True),
        404: 'Not Found - post no trobat'
    }
)
@api_view(['GET'])
def post_comments_tree(request, pk):
    """
    GET /api/posts/{id}/comments/tree/
    Retorna els comentaris en estructura d'arbre amb tots els nivells de respostes.
    """
    post = get_object_or_404(Post, pk=pk)
    root_comments = Comment.objects.filter(post=post, parent__isnull=True).order_by('published_date')
    serializer = CommentTreeSerializer(root_comments, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    operation_description="Retorna només els comentaris de primer nivell d'un post (sense respostes)",
    responses={
        200: CommentTreeSerializer(many=True),
        404: 'Not Found - post no trobat'
    }
)
@api_view(['GET'])
def post_comments_root(request, pk):
    """
    GET /api/posts/{id}/comments/root/
    Retorna només els comentaris pare (primer nivell) sense incloure les respostes.
    """
    post = get_object_or_404(Post, pk=pk)
    root_comments = Comment.objects.filter(post=post, parent__isnull=True).order_by('published_date')
    serializer = CommentTreeSerializer(root_comments, many=True)
    for c in serializer.data:
        c['replies'] = []
    return Response(serializer.data)


# Paràmetres per la cerca
query_param = openapi.Parameter(
    'q', openapi.IN_QUERY,
    description="Text a cercar en títols de posts o contingut de comentaris",
    type=openapi.TYPE_STRING,
    required=True
)
type_param = openapi.Parameter(
    'type', openapi.IN_QUERY,
    description="Tipus de cerca: 'posts' (només posts), 'comments' (només comentaris), o 'both' (ambdós)",
    type=openapi.TYPE_STRING,
    required=False,
    default='both',
    enum=['posts', 'comments', 'both']
)

@swagger_auto_schema(
    method='get',
    manual_parameters=[query_param, type_param],
    operation_description="Cerca posts i/o comentaris pel text indicat. Retorna resultats ordenats per data de publicació (més recents primer)",
    responses={
        200: openapi.Response(
            description="Posts i/o comentaris trobats",
            examples={
                'application/json': {
                    "query": "exemple",
                    "type": "both",
                    "posts": [],
                    "comments": []
                }
            }
        ),
        400: 'Bad Request - cal especificar el paràmetre q'
    }
)
@api_view(['GET'])
def search_posts_comments(request):
    """
    GET /api/search/?q=text&type=both
    Cerca posts per títol i comentaris per contingut.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'both').lower()

    if not query:
        return Response({"error": "Cal especificar el paràmetre q"}, status=400)

    if search_type not in ['posts', 'comments', 'both']:
        return Response({"error": "El paràmetre type ha de ser 'posts', 'comments' o 'both'"}, status=400)

    result = {}
    if search_type in ['posts', 'both']:
        posts = Post.objects.prefetch_related('communities').filter(title__icontains=query).order_by('-published_date')
        result['posts'] = PostSerializer(posts, many=True).data
    if search_type in ['comments', 'both']:
        comments = Comment.objects.filter(content__icontains=query).order_by('-published_date')
        result['comments'] = CommentSerializer(comments, many=True).data

    return Response({"query": query, "type": search_type, **result})
