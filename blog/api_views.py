# flake8: noqa E501
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post, Comment, VoteComment, VotePost
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
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
    PostDeleteSerializer,
    CommentCreateSerializer,
    CommentEditSerializer,
)

# -------------------- POST VIEWS --------------------

@extend_schema(
    summary="Llista de posts",
    description="""
    Retorna la llista de tots els posts amb les seves comunitats associades.
    
    **Paràmetres d'ordenació (order):**
    - `new` (defecte): Ordena del més recent al més antic per data de publicació
    - `old`: Ordena del més antic al més recent per data de publicació
    - `comments`: Ordena per nombre de comentaris (de més a menys). Els posts amb el mateix nombre de comentaris s'ordenen per data (més recents primer)
    - `votes`: Ordena per nombre de vots (de més a menys). Els posts amb els mateixos vots s'ordenen per data (més recents primer)
    
    **Paràmetres de filtratge (filter):**
    - `all` (defecte): Retorna tots els posts sense filtre
    - `subscribed`: Retorna només posts de comunitats a les quals l'usuari està subscrit. **Requereix autenticació**
    - `local`: Retorna només posts de comunitats a les quals l'usuari NO està subscrit. **Requereix autenticació**
    
    **Exemples d'ús:**
    - `/api/posts/` - Posts més recents (comportament per defecte)
    - `/api/posts/?order=votes` - Posts ordenats per vots
    - `/api/posts/?filter=subscribed&order=comments` - Posts de comunitats subscrites ordenats per nombre de comentaris
    - `/api/posts/?filter=local&order=new` - Posts de comunitats no subscrites (locals) ordenats per data
    
    **Notes:**
    - Els paràmetres són opcionals. Si no s'especifiquen, s'utilitzen els valors per defecte (order=new, filter=all)
    - Els filtres 'subscribed' i 'local' retornen un error 401 si l'usuari no està autenticat
    - Si un post pertany a múltiples comunitats, només apareixerà una vegada als resultats
    """,
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació dels posts",
            enum=['new', 'old', 'comments', 'votes'],
            default='new',
            required=False
        ),
        OpenApiParameter(
            name='filter',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtre per tipus de comunitat (subscribed i local requereixen autenticació)",
            enum=['all', 'subscribed', 'local'],
            default='all',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=PostSerializer(many=True),
            description="Llista de posts retornada correctament"
        ),
        400: OpenApiResponse(
            description="Bad Request - Paràmetres invàlids",
            examples=[
                OpenApiExample(
                    'Error paràmetre order invàlid',
                    value={"error": "Paràmetre 'order' invàlid. Valors permesos: new, old, comments, votes"},
                    response_only=True
                ),
                OpenApiExample(
                    'Error paràmetre filter invàlid',
                    value={"error": "Paràmetre 'filter' invàlid. Valors permesos: all, subscribed, local"},
                    response_only=True
                )
            ]
        ),
        401: OpenApiResponse(
            description="Unauthorized - Autenticació requerida per utilitzar filtres subscribed o local",
            examples=[
                OpenApiExample(
                    'Error autenticació requerida',
                    value={"error": "Cal autenticació per utilitzar els filtres 'subscribed' o 'local'"},
                    response_only=True
                )
            ]
        ),
        500: OpenApiResponse(
            description="Error intern del servidor",
            examples=[
                OpenApiExample(
                    'Error del servidor',
                    value={"error": "S'ha produït un error inesperat al servidor"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Posts']
)
@api_view(['GET'])
def post_list(request):
    """
    GET /api/posts/?order=new&filter=all
    Retorna tots els posts amb informació de les comunitats a les quals pertanyen.
    
    Paràmetres:
    - order: new (defecte), old, comments, votes
    - filter: all (defecte), subscribed, local (requereix autenticació)
    """
    # Obtenir paràmetres
    order = request.GET.get('order', 'new').lower()
    filter_type = request.GET.get('filter', 'all').lower()
    
    # Validar paràmetres
    valid_orders = ['new', 'old', 'comments', 'votes']
    valid_filters = ['all', 'subscribed', 'local']
    
    if order not in valid_orders:
        return Response({
            "error": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    if filter_type not in valid_filters:
        return Response({
            "error": f"Paràmetre 'filter' invàlid. Valors permesos: {', '.join(valid_filters)}"
        }, status=400)
    
    # Filtres subscribed i local requereixen autenticació
    if filter_type in ['subscribed', 'local'] and not request.user.is_authenticated:
        return Response({
            "error": "Cal autenticació per utilitzar els filtres 'subscribed' o 'local'"
        }, status=401)
    
    # Començar amb tots els posts
    posts = Post.objects.prefetch_related('communities').all()
    
    # Aplicar filtre
    if filter_type == 'subscribed' and request.user.is_authenticated:
        # Posts de comunitats a les quals l'usuari està subscrit
        user_communities = request.user.subscribed_communities.all()
        posts = posts.filter(communities__in=user_communities).distinct()
    
    elif filter_type == 'local' and request.user.is_authenticated:
        # Posts de comunitats a les quals l'usuari NO està subscrit
        user_communities = request.user.subscribed_communities.all()
        posts = posts.exclude(communities__in=user_communities).distinct()
    
    # Aplicar ordenació
    if order == 'new':
        posts = posts.order_by('-published_date')
    elif order == 'old':
        posts = posts.order_by('published_date')
    elif order == 'comments':
        posts = posts.annotate(comment_count=Count('comments')).order_by('-comment_count', '-published_date')
    elif order == 'votes':
        posts = posts.order_by('-votes', '-published_date')
    
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Detall d'un post",
    description="Retorna la informació detallada d'un post concret amb totes les seves dades i comunitats associades",
    responses={
        200: PostSerializer,
        404: OpenApiResponse(description='Post no trobat')
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


class PostCreateAPIView(generics.GenericAPIView):
    serializer_class = PostCreateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=PostCreateSerializer,
        responses={201: PostSerializer},
        description="""
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

    @extend_schema(
        request=PostUpdateSerializer,
        responses={200: PostSerializer},
        description="Actualitza els camps enviats del post (formData amb fitxers i text)",
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

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Post eliminat correctament"),
            404: OpenApiResponse(description="Post no trobat"),
            401: OpenApiResponse(description="No autenticat"),
            403: OpenApiResponse(description="No tens permís per eliminar aquest post")
        },
        description="Elimina un post concret (només l'autor pot eliminar-lo)",
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

    @extend_schema(
        responses={200: OpenApiResponse(description="Número de vots actual del post")},
        description="Dóna un vot positiu (upvote) al post",
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

    @extend_schema(
        responses={200: OpenApiResponse(description="Número de vots actual del post")},
        description="Dóna un vot negatiu (downvote) al post",
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

@extend_schema(
    summary="Comentaris d'un post",
    description="""
    Retorna tots els comentaris d'un post concret (llista plana sense jerarquia).
    
    **Paràmetres d'ordenació (order):**
    - `new` (defecte): Ordena del més recent al més antic per data de publicació
    - `old`: Ordena del més antic al més recent per data de publicació
    - `top`: Ordena per nombre de vots (de més a menys). Els comentaris amb els mateixos vots s'ordenen per data (més recents primer)
    
    **Exemples d'ús:**
    - `/api/posts/1/comments/` - Comentaris més recents (comportament per defecte)
    - `/api/posts/1/comments/?order=top` - Comentaris ordenats per vots
    - `/api/posts/1/comments/?order=old` - Comentaris més antics primer
    """,
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació dels comentaris",
            enum=['new', 'old', 'top'],
            default='new',
            required=False
        ),
    ],
    responses={
        200: CommentSerializer(many=True),
        400: OpenApiResponse(
            description="Bad Request - Paràmetre invàlid",
            examples=[
                OpenApiExample(
                    'Error paràmetre order invàlid',
                    value={"error": "Paràmetre 'order' invàlid. Valors permesos: new, old, top"},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(description='Post no trobat')
    },
    tags=['Comments']
)
@api_view(['GET'])
def post_comments(request, pk):
    """
    GET /api/posts/{id}/comments/?order=new
    Retorna tots els comentaris (plana sense jerarquia) d'un post amb ordenació.
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Obtenir paràmetre d'ordenació
    order = request.GET.get('order', 'new').lower()
    
    # Validar paràmetre
    valid_orders = ['new', 'old', 'top']
    if order not in valid_orders:
        return Response({
            "error": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    # Obtenir comentaris
    comments = Comment.objects.filter(post=post)
    
    # Aplicar ordenació
    if order == 'new':
        comments = comments.order_by('-published_date')
    elif order == 'old':
        comments = comments.order_by('published_date')
    elif order == 'top':
        comments = comments.order_by('-votes', '-published_date')
    
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Comentaris en arbre d'un post",
    description="""
    Retorna els comentaris d'un post amb estructura jeràrquica en arbre. Els comentaris fills apareixen dins del camp 'replies' de cada comentari pare.
    
    **Paràmetres d'ordenació (order):**
    - `new` (defecte): Ordena del més recent al més antic per data de publicació
    - `old`: Ordena del més antic al més recent per data de publicació
    - `top`: Ordena per nombre de vots (de més a menys). Els comentaris amb els mateixos vots s'ordenen per data (més recents primer)
    
    **Notes:**
    - L'ordenació s'aplica a tots els nivells de l'arbre de comentaris
    - Els comentaris fills (replies) també segueixen el mateix criteri d'ordenació
    
    **Exemples d'ús:**
    - `/api/posts/1/comments/tree/` - Comentaris més recents en arbre
    - `/api/posts/1/comments/tree/?order=top` - Comentaris ordenats per vots en arbre
    """,
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació dels comentaris",
            enum=['new', 'old', 'top'],
            default='new',
            required=False
        ),
    ],
    responses={
        200: CommentTreeSerializer(many=True),
        400: OpenApiResponse(
            description="Bad Request - Paràmetre invàlid",
            examples=[
                OpenApiExample(
                    'Error paràmetre order invàlid',
                    value={"error": "Paràmetre 'order' invàlid. Valors permesos: new, old, top"},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(description='Post no trobat')
    },
    tags=['Comments']
)
@api_view(['GET'])
def post_comments_tree(request, pk):
    """
    GET /api/posts/{id}/comments/tree/?order=new
    Retorna els comentaris en estructura d'arbre amb tots els nivells de respostes.
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Obtenir paràmetre d'ordenació
    order = request.GET.get('order', 'new').lower()
    
    # Validar paràmetre
    valid_orders = ['new', 'old', 'top']
    if order not in valid_orders:
        return Response({
            "error": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    # Obtenir comentaris root
    root_comments = Comment.objects.filter(post=post, parent__isnull=True)
    
    # Aplicar ordenació
    if order == 'new':
        root_comments = root_comments.order_by('-published_date')
    elif order == 'old':
        root_comments = root_comments.order_by('published_date')
    elif order == 'top':
        root_comments = root_comments.order_by('-votes', '-published_date')
    
    serializer = CommentTreeSerializer(root_comments, many=True, context={'order': order})
    return Response(serializer.data)


@extend_schema(
    summary="Comentaris de primer nivell d'un post",
    description="""
    Retorna només els comentaris de primer nivell (root) d'un post, sense incloure les respostes. El camp 'replies' estarà buit per a tots els comentaris.
    
    **Paràmetres d'ordenació (order):**
    - `new` (defecte): Ordena del més recent al més antic per data de publicació
    - `old`: Ordena del més antic al més recent per data de publicació
    - `top`: Ordena per nombre de vots (de més a menys). Els comentaris amb els mateixos vots s'ordenen per data (més recents primer)
    
    **Exemples d'ús:**
    - `/api/posts/1/comments/root/` - Comentaris de primer nivell més recents
    - `/api/posts/1/comments/root/?order=top` - Comentaris de primer nivell ordenats per vots
    """,
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació dels comentaris",
            enum=['new', 'old', 'top'],
            default='new',
            required=False
        ),
    ],
    responses={
        200: CommentTreeSerializer(many=True),
        400: OpenApiResponse(
            description="Bad Request - Paràmetre invàlid",
            examples=[
                OpenApiExample(
                    'Error paràmetre order invàlid',
                    value={"error": "Paràmetre 'order' invàlid. Valors permesos: new, old, top"},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(description='Post no trobat')
    },
    tags=['Comments']
)
@api_view(['GET'])
def post_comments_root(request, pk):
    """
    GET /api/posts/{id}/comments/root/?order=new
    Retorna només els comentaris pare (primer nivell) sense incloure les respostes.
    """
    post = get_object_or_404(Post, pk=pk)
    
    # Obtenir paràmetre d'ordenació
    order = request.GET.get('order', 'new').lower()
    
    # Validar paràmetre
    valid_orders = ['new', 'old', 'top']
    if order not in valid_orders:
        return Response({
            "error": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    # Obtenir comentaris root
    root_comments = Comment.objects.filter(post=post, parent__isnull=True)
    
    # Aplicar ordenació
    if order == 'new':
        root_comments = root_comments.order_by('-published_date')
    elif order == 'old':
        root_comments = root_comments.order_by('published_date')
    elif order == 'top':
        root_comments = root_comments.order_by('-votes', '-published_date')
    
    serializer = CommentTreeSerializer(root_comments, many=True)
    for c in serializer.data:
        c['replies'] = []
    return Response(serializer.data)

class CommentCreateAPIView(generics.GenericAPIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = CommentCreateSerializer

    @extend_schema(
        request=CommentCreateSerializer,
        responses={201: CommentSerializer},
        description="Crea un comentari en un post. Suporta parent_id per crear respostes a altres comentaris i permet pujar una imatge",
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


   @extend_schema(
       request=CommentEditSerializer,
       responses={
           200: CommentSerializer,
           403: OpenApiResponse(description="No tens permís per editar aquest comentari")
       },
       description="Edita un comentari existent. Permet modificar el contingut i/o la imatge. Només l'autor pot editar el seu comentari",
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

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Comentari eliminat correctament"),
            404: OpenApiResponse(description="Comentari no trobat"),
            401: OpenApiResponse(description="No autenticat"),
            403: OpenApiResponse(description="No tens permís per eliminar aquest comentari")
        },
        description="Elimina un comentari concret. Només l'autor pot eliminar el seu propi comentari",
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

    @extend_schema(
        responses={200: OpenApiResponse(description="Número de vots actual del comentari")},
        description="Dóna un vot positiu (upvote) al comentari",
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

    @extend_schema(
        responses={200: OpenApiResponse(description="Número de vots actual del comentari")},
        description="Dóna un vot negatiu (downvote) al comentari",
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

@extend_schema(
    summary="Cerca posts i comentaris",
    description="""
    Cerca posts i/o comentaris pel text indicat. 
    
    **Cerca en posts:** Busca coincidències al títol del post
    **Cerca en comentaris:** Busca coincidències al contingut del comentari
    
    Els resultats es retornen ordenats per data de publicació (més recents primer)
    """,
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Text a cercar en títols de posts o contingut de comentaris",
            required=True
        ),
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Tipus de cerca",
            enum=['posts', 'comments', 'both'],
            default='both',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Posts i/o comentaris trobats",
            examples=[
                OpenApiExample(
                    'Exemple de cerca',
                    value={
                        "query": "exemple",
                        "type": "both",
                        "posts": [],
                        "comments": []
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='Bad Request - cal especificar el paràmetre q',
            examples=[
                OpenApiExample(
                    'Error paràmetre q buit',
                    value={"error": "Cal especificar el paràmetre q"}
                ),
                OpenApiExample(
                    'Error paràmetre type invàlid',
                    value={"error": "El paràmetre type ha de ser 'posts', 'comments' o 'both'"}
                )
            ]
        )
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