# flake8: noqa E501
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post, Comment, VoteComment, VotePost
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import APIKeyAuthentication
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import (
    PostSerializer,
    PostCreateSerializer,
    CommentSerializer,
    CommentTreeSerializer,
    PostUpdateSerializer,
)

# -------------------- POST VIEWS --------------------

@swagger_auto_schema(
    method='get',
    operation_description="Retorna la llista de tots els posts amb les seves comunitats",
    responses={
        200: PostSerializer(many=True),
        500: 'Error intern del servidor'
    },
    tags=['Posts']
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
    },
    tags=['Posts']
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


class PostCreateAPIView(generics.CreateAPIView):
    """
    API endpoint per crear un post nou.
    Omple els camps del formulari per crear el teu post.
    """
    serializer_class = PostCreateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        Crea un post nou amb els següents camps:
        - **title**: Títol del post (obligatori, màxim 200 caràcters)
        - **content**: Contingut del post (obligatori)
        - **url**: Enllaç d'interès (opcional)
        - **image**: Fitxer d'imatge (opcional)
        - **communities**: IDs de les comunitats (opcional, pots seleccionar múltiples)
        """,
        request_body=PostCreateSerializer,
        responses={
            201: openapi.Response(
                description="Post creat correctament",
                schema=PostSerializer
            ),
            400: "Dades invàlides",
            401: "No autenticat"
        },
        tags=['Posts']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        post = serializer.instance
        output_serializer = PostSerializer(post)
        return Response(output_serializer.data, status=201)


class PostEditAPIView(generics.GenericAPIView):
    queryset = Post.objects.all()
    serializer_class = PostUpdateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        return get_object_or_404(Post, pk=pk)

    @swagger_auto_schema(
        responses={200: PostUpdateSerializer},
        operation_description="Mostra els valors actuals del post per editar",
        tags=['Posts']
    )
    def get(self, request, pk):
        post = self.get_object(pk)
        serializer = PostUpdateSerializer(post)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=PostUpdateSerializer,
        responses={200: PostSerializer},
        operation_description="Actualitza els camps enviats del post (formData amb fitxers i text)",
        tags=['Posts']
    )
    def put(self, request, pk):
        post = self.get_object(pk)
        serializer = PostUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = PostSerializer(post)
        return Response(output_serializer.data)

class UpvotePostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: "Número de vots actual del post"},
        operation_description="Dóna un vot positiu (upvote) al post",
        tags=['Posts']
    )
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        vote_obj, _ = VotePost.objects.get_or_create(user=request.user, post=post)

        if vote_obj.vote != 1:
            if vote_obj.vote == -1:
                post.votes += 2
            else:
                post.votes += 1
            vote_obj.vote = 1
            vote_obj.save()
            post.save()

        return Response({"votes": post.votes})


class DownvotePostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: "Número de vots actual del post"},
        operation_description="Dóna un vot negatiu (downvote) al post",
        tags=['Posts']
    )
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        vote_obj, _ = VotePost.objects.get_or_create(user=request.user, post=post)

        if vote_obj.vote != -1:
            if vote_obj.vote == 1:
                post.votes -= 2
            else:
                post.votes -= 1
            vote_obj.vote = -1
            vote_obj.save()
            post.save()

        return Response({"votes": post.votes})

# -------------------- COMMENT VIEWS --------------------

@swagger_auto_schema(
    method='get',
    operation_description="Retorna tots els comentaris d'un post concret ordenats per data de publicació",
    responses={
        200: CommentSerializer(many=True),
        404: 'Not Found - post no trobat'
    },
    tags=['Comments']
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
    },
    tags=['Comments']
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
    },
    tags=['Comments']
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


class UpvoteCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: "Número de vots actual del comentari"},
        operation_description="Dóna un vot positiu (upvote) al comentari",
        tags=['Comments']
    )
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        vote_obj, _ = VoteComment.objects.get_or_create(user=request.user, comment=comment)

        if vote_obj.vote != 1:
            if vote_obj.vote == -1:
                comment.votes += 2
            else:
                comment.votes += 1
            vote_obj.vote = 1
            vote_obj.save()
            comment.save()

        return Response({"votes": comment.votes})


class DownvoteCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: "Número de vots actual del comentari"},
        operation_description="Dóna un vot negatiu (downvote) al comentari",
        tags=['Comments']
    )
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        vote_obj, _ = VoteComment.objects.get_or_create(user=request.user, comment=comment)

        if vote_obj.vote != -1:
            if vote_obj.vote == 1:
                comment.votes -= 2
            else:
                comment.votes -= 1
            vote_obj.vote = -1
            vote_obj.save()
            comment.save()

        return Response({"votes": comment.votes})


# -------------------- SEARCH --------------------

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
    },
    tags=['Search']
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