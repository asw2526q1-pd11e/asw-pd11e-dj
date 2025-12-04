# flake8: noqa E501
from django.shortcuts import get_object_or_404
from django.utils import timezone
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
from rest_framework import status
from django.db.models import Count

from .serializers import (
    PostSerializer,
    PostCreateSerializer,
    CommentSerializer,
    CommentTreeSerializer,
    PostUpdateSerializer,
    PostDeleteSerializer,
    CommentCreateSerializer,
    CommentEditSerializer,
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


order_param = openapi.Parameter(
    'order',
    openapi.IN_QUERY,
    description="Criteri d'ordenació: 'nou', 'antic', 'mes_comentaris', 'mes_vots'",
    type=openapi.TYPE_STRING,
    required=False,
    enum=['nou', 'antic', 'mes_comentaris', 'mes_vots']
)

@swagger_auto_schema(
    method='get',
    manual_parameters=[order_param],
    operation_id="blog_posts_order",
    operation_description="Retorna la llista de posts ordenats segons el criteri indicat.",
    responses={200: PostSerializer(many=True)},
    tags=['Posts']
)
@api_view(['GET'])
def post_list_ordered(request):
    """
    GET /api/blog/posts/?order=nou|antic|mes_comentaris|mes_vots
    Retorna els posts ordenats.
    """

    order = request.GET.get("order", "nou")

    if order == "nou":
        posts = Post.objects.all().order_by("-published_date")
    elif order == "antic":
        posts = Post.objects.all().order_by("published_date")
    elif order == "mes_comentaris":
        posts = Post.objects.annotate(num_comments=Count('comments')).order_by("-num_comments")
    elif order == "mes_vots":
        posts = Post.objects.all().order_by("-votes")
    else:
        posts = Post.objects.all().order_by("-published_date")

    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


class PostCreateAPIView(generics.GenericAPIView):
    serializer_class = PostCreateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=PostCreateSerializer,
        responses={200: PostSerializer},
        operation_description="""
        Crea un post nou amb els següents camps:
        - title: Títol del post (obligatori)
        - content: Contingut del post (obligatori)
        - url: Enllaç d'interès (opcional)
        - image: Fitxer d'imatge (opcional)
        - communities: IDs de les comunitats (opcional)
        """,
        tags=['Posts']
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Assignem l'autor
        post = serializer.save(author=request.user)

        # Serialitzador de sortida
        output_serializer = PostSerializer(post)
        return Response(output_serializer.data, status=201)



class PostEditAPIView(generics.GenericAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    queryset = Post.objects.none()

    def get_object(self, pk):
        return get_object_or_404(Post, pk=pk)

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


class DeletePostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            204: PostDeleteSerializer,
            404: "Post no trobat",
            401: "No autenticat"
        },
        operation_description="Elimina un post concret (només l'autor pot eliminar-lo)",
        tags=['Posts']
    )

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)

        if post.author != request.user:
            return Response({"detail": "No tens permís per eliminar aquest post."}, status=403)

        post.delete()
        return Response(status=204)


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

class CommentCreateAPIView(generics.GenericAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = CommentCreateSerializer

    @swagger_auto_schema(
        request_body=CommentCreateSerializer,
        responses={201: CommentSerializer},
        operation_description="Crea un comentario en un post. Soporta parent_id e imagen.",
        tags=['Comments']
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        parent_comment = None
        parent_id = data.get("parent_id")
        if parent_id:
            parent_comment = get_object_or_404(Comment, pk=parent_id, post=post)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=data["content"],
            parent=parent_comment,
            image=data.get("image"),
            published_date=timezone.now(),
            votes=0,
        )

        return Response(CommentSerializer(comment).data, status=201)

class CommentEditAPIView(generics.GenericAPIView):
   authentication_classes = [APIKeyAuthentication]
   permission_classes = [IsAuthenticated]
   parser_classes = [MultiPartParser, FormParser]
   serializer_class = CommentEditSerializer
   queryset = Comment.objects.none()


   def get_object(self, comment_id):
       return get_object_or_404(Comment, pk=comment_id)


   @swagger_auto_schema(
       request_body=CommentEditSerializer,
       responses={200: CommentSerializer},
       operation_description="Edita un comentari existent. Permet modificar el contingut i/o la imatge.",
       tags=["Comments"],
   )
   def put(self, request, comment_id):
       comment = self.get_object(comment_id)


       # Comprovem autor
       if comment.author != request.user:
           return Response(
               {"detail": "No tens permís per editar aquest comentari."}, status=403
           )


       serializer = CommentEditSerializer(comment, data=request.data, partial=True)
       serializer.is_valid(raise_exception=True)
       serializer.save()


       return Response(CommentSerializer(comment).data, status=200)


class DeleteCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            204: "Comentari eliminat correctament",
            404: "Comentari no trobat",
            401: "No autenticat",
            403: "No tens permís per eliminar aquest comentari"
        },
        operation_description="Elimina un comentari concret (només l'autor pot eliminar-lo)",
        tags=['Comments']
    )
    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)

        # Comprovem que l'autor és el mateix usuari autenticat
        if comment.author != request.user:
            return Response({"detail": "No tens permís per eliminar aquest comentari."}, status=403)

        comment.delete()
        return Response(status=204)


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