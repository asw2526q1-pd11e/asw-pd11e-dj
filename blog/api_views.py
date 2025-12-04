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
    description=(
        "Retorna la llista de tots els posts amb les seves comunitats associades.\n"
        "\n"
        "**Paràmetres d'ordenació (order):**\n"
        "- **new** (defecte): Ordena del més recent al més antic per data de publicació\n"
        "- **old**: Ordena del més antic al més recent per data de publicació\n"
        "- **comments**: Ordena per nombre de comentaris (de més a menys)\n"
        "- **votes**: Ordena per nombre de vots (de més a menys)\n"
        "\n"
        "**Paràmetres de filtratge (filter):**\n"
        "- **all** (defecte): Retorna tots els posts sense filtre\n"
        "- **subscribed**: Només posts de comunitats subscrites (requereix autenticació)\n"
        "- **local**: Només posts de comunitats NO subscrites (requereix autenticació)"
    ),
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
            description="Filtre per tipus de comunitat",
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
            description="Paràmetres invàlids",
            examples=[
                OpenApiExample(
                    'Error order invàlid',
                    value={"detail": "Paràmetre 'order' invàlid. Valors permesos: new, old, comments, votes"},
                    response_only=True
                ),
                OpenApiExample(
                    'Error filter invàlid',
                    value={"detail": "Paràmetre 'filter' invàlid. Valors permesos: all, subscribed, local"},
                    response_only=True
                )
            ]
        ),
        401: OpenApiResponse(
            description="Cal autenticació",
            examples=[
                OpenApiExample(
                    'No autenticat',
                    value={"detail": "Cal autenticació per utilitzar els filtres 'subscribed' o 'local'"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Posts']
)
@api_view(['GET'])
def post_list(request):
    order = request.GET.get('order', 'new').lower()
    filter_type = request.GET.get('filter', 'all').lower()
    
    valid_orders = ['new', 'old', 'comments', 'votes']
    valid_filters = ['all', 'subscribed', 'local']
    
    if order not in valid_orders:
        return Response({
            "detail": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    if filter_type not in valid_filters:
        return Response({
            "detail": f"Paràmetre 'filter' invàlid. Valors permesos: {', '.join(valid_filters)}"
        }, status=400)
    
    if filter_type in ['subscribed', 'local'] and not request.user.is_authenticated:
        return Response({
            "detail": "Cal autenticació per utilitzar els filtres 'subscribed' o 'local'"
        }, status=401)
    
    posts = Post.objects.prefetch_related('communities').all()
    
    if filter_type == 'subscribed' and request.user.is_authenticated:
        user_communities = request.user.subscribed_communities.all()
        posts = posts.filter(communities__in=user_communities).distinct()
    
    elif filter_type == 'local' and request.user.is_authenticated:
        user_communities = request.user.subscribed_communities.all()
        posts = posts.exclude(communities__in=user_communities).distinct()
    
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
    description="Retorna la informació detallada d'un post concret",
    responses={
        200: PostSerializer,
        404: OpenApiResponse(
            description="Post no trobat",
            examples=[
                OpenApiExample(
                    'Post inexistent',
                    value={"detail": "Post no trobat"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Posts']
)
@api_view(['GET'])
def post_detail(request, pk):
    try:
        post = Post.objects.prefetch_related('communities').get(pk=pk)
    except Post.DoesNotExist:
        return Response({"detail": "Post no trobat"}, status=404)
    serializer = PostSerializer(post)
    return Response(serializer.data)


class PostCreateAPIView(generics.GenericAPIView):
    serializer_class = PostCreateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Crea un nou post",
        request=PostCreateSerializer,
        responses={
            201: PostSerializer,
            400: OpenApiResponse(
                description="Dades invàlides",
                examples=[
                    OpenApiExample(
                        'Camp obligatori buit',
                        value={"detail": {"title": ["Aquest camp és obligatori"]}},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Comunitat inexistent',
                        value={"detail": "Una o més comunitats especificades no existeixen"},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            )
        },
        description=(
            "Crea un post nou:\n"
            "- title: Títol (obligatori, màx 200 caràcters)\n"
            "- content: Contingut (obligatori, màx 5000 caràcters)\n"
            "- url: Enllaç (opcional)\n"
            "- image: Imatge (opcional)\n"
            "- communities: IDs comunitats (opcional)"
        ),
        tags=['Posts']
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
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
        summary="Edita un post existent",
        request=PostUpdateSerializer,
        responses={
            200: PostSerializer,
            400: OpenApiResponse(
                description="Dades invàlides",
                examples=[
                    OpenApiExample(
                        'Camp massa llarg',
                        value={"detail": {"title": ["Assegureu-vos que aquest camp no tingui més de 200 caràcters"]}},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Sense permís",
                examples=[
                    OpenApiExample(
                        'No és l\'autor',
                        value={"detail": "No tens permís per editar aquest post"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Post no trobat",
                examples=[
                    OpenApiExample(
                        'Post inexistent',
                        value={"detail": "Post no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description=(
            "Actualitza els camps enviats del post (només l'autor).\n"
            "\n"
            "**Nota:** Només s'actualitzen els camps que s'envien amb valors no buits.\n"
            "Els camps buits o no enviats es mantenen sense canvis."
        ),
        tags=['Posts']
    )
    def put(self, request, pk):
        post = self.get_object(pk)
        
        if post.author != request.user:
            return Response({"detail": "No tens permís per editar aquest post"}, status=403)
        
        # Filtrar camps buits de request.data
        cleaned_data = {}
        for key, value in request.data.items():
            # Només afegir si el valor no és buit
            if value not in ['', None, 'null']:
                # Per a camps de text, verificar que no siguin només espais en blanc
                if isinstance(value, str) and value.strip() == '':
                    continue
                cleaned_data[key] = value
        
        # Si no hi ha res a actualitzar, retornar el post sense canvis
        if not cleaned_data:
            output_serializer = PostSerializer(post)
            return Response(output_serializer.data)
        
        serializer = PostUpdateSerializer(post, data=cleaned_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = PostSerializer(post)
        return Response(output_serializer.data)

class DeletePostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Elimina un post",
        responses={
            204: OpenApiResponse(description="Post eliminat correctament"),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Sense permís",
                examples=[
                    OpenApiExample(
                        'No és l\'autor',
                        value={"detail": "No tens permís per eliminar aquest post"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Post no trobat",
                examples=[
                    OpenApiExample(
                        'Post inexistent',
                        value={"detail": "Post no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Elimina un post (només l'autor)",
        tags=['Posts']
    )
    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        if post.author != request.user:
            return Response({"detail": "No tens permís per eliminar aquest post"}, status=403)
        post.delete()
        return Response({"detail": "Post eliminat correctament"}, status=204)


class UpvotePostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dóna un upvote al post",
        responses={
            200: OpenApiResponse(
                description="Vot registrat correctament",
                examples=[
                    OpenApiExample(
                        'Vots actualitzats',
                        value={"votes": 42},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Post no trobat",
                examples=[
                    OpenApiExample(
                        'Post inexistent',
                        value={"detail": "Post no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Dóna un upvote al post",
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
        else:
            # quitar voto (toggle off)
            vote_obj.vote = 0
            vote_obj.save()
            post.votes -= 1
            post.save()
        return Response({"votes": post.votes})


class DownvotePostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dóna un downvote al post",
        responses={
            200: OpenApiResponse(
                description="Vot registrat correctament",
                examples=[
                    OpenApiExample(
                        'Vots actualitzats',
                        value={"votes": 38},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Post no trobat",
                examples=[
                    OpenApiExample(
                        'Post inexistent',
                        value={"detail": "Post no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Dóna un downvote al post",
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
        else:
            # quitar voto (toggle off)
            vote_obj.vote = 0
            vote_obj.save()
            post.votes += 1
            post.save()
        return Response({"votes": post.votes})

# -------------------- COMMENT VIEWS --------------------

@extend_schema(
    summary="Comentaris d'un post",
    description=(
        "Retorna tots els comentaris (llista plana).\n"
        "\n"
        "**Ordenació (order):**\n"
        "- **new** (defecte): Més recents primer\n"
        "- **old**: Més antics primer\n"
        "- **top**: Més votats primer"
    ),
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació",
            enum=['new', 'old', 'top'],
            default='new',
            required=False
        ),
    ],
    responses={
        200: CommentSerializer(many=True),
        400: OpenApiResponse(
            description="Paràmetre invàlid",
            examples=[
                OpenApiExample(
                    'Order invàlid',
                    value={"detail": "Paràmetre 'order' invàlid. Valors permesos: new, old, top"},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(
            description="Post no trobat",
            examples=[
                OpenApiExample(
                    'Post inexistent',
                    value={"detail": "Post no trobat"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Comments']
)
@api_view(['GET'])
def post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    order = request.GET.get('order', 'new').lower()
    
    valid_orders = ['new', 'old', 'top']
    if order not in valid_orders:
        return Response({
            "detail": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    comments = Comment.objects.filter(post=post)
    
    if order == 'new':
        comments = comments.order_by('-published_date')
    elif order == 'old':
        comments = comments.order_by('published_date')
    elif order == 'top':
        comments = comments.order_by('-votes', '-published_date')
    
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@extend_schema(
    summary="Comentaris en arbre",
    description=(
        "Retorna comentaris amb estructura jeràrquica.\n"
        "\n"
        "**Ordenació (order):**\n"
        "- **new** (defecte): Més recents primer\n"
        "- **old**: Més antics primer\n"
        "- **top**: Més votats primer"
    ),
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació",
            enum=['new', 'old', 'top'],
            default='new',
            required=False
        ),
    ],
    responses={
        200: CommentTreeSerializer(many=True),
        400: OpenApiResponse(
            description="Paràmetre invàlid",
            examples=[
                OpenApiExample(
                    'Order invàlid',
                    value={"detail": "Paràmetre 'order' invàlid. Valors permesos: new, old, top"},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(
            description="Post no trobat",
            examples=[
                OpenApiExample(
                    'Post inexistent',
                    value={"detail": "Post no trobat"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Comments']
)
@api_view(['GET'])
def post_comments_tree(request, pk):
    post = get_object_or_404(Post, pk=pk)
    order = request.GET.get('order', 'new').lower()
    
    valid_orders = ['new', 'old', 'top']
    if order not in valid_orders:
        return Response({
            "detail": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    root_comments = Comment.objects.filter(post=post, parent__isnull=True)
    
    if order == 'new':
        root_comments = root_comments.order_by('-published_date')
    elif order == 'old':
        root_comments = root_comments.order_by('published_date')
    elif order == 'top':
        root_comments = root_comments.order_by('-votes', '-published_date')
    
    serializer = CommentTreeSerializer(root_comments, many=True, context={'order': order})
    return Response(serializer.data)


@extend_schema(
    summary="Comentaris de primer nivell",
    description=(
        "Retorna només comentaris root (sense replies).\n"
        "\n"
        "**Ordenació (order):**\n"
        "- **new** (defecte): Més recents primer\n"
        "- **old**: Més antics primer\n"
        "- **top**: Més votats primer"
    ),
    parameters=[
        OpenApiParameter(
            name='order',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Criteri d'ordenació",
            enum=['new', 'old', 'top'],
            default='new',
            required=False
        ),
    ],
    responses={
        200: CommentTreeSerializer(many=True),
        400: OpenApiResponse(
            description="Paràmetre invàlid",
            examples=[
                OpenApiExample(
                    'Order invàlid',
                    value={"detail": "Paràmetre 'order' invàlid. Valors permesos: new, old, top"},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(
            description="Post no trobat",
            examples=[
                OpenApiExample(
                    'Post inexistent',
                    value={"detail": "Post no trobat"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Comments']
)
@api_view(['GET'])
def post_comments_root(request, pk):
    post = get_object_or_404(Post, pk=pk)
    order = request.GET.get('order', 'new').lower()
    
    valid_orders = ['new', 'old', 'top']
    if order not in valid_orders:
        return Response({
            "detail": f"Paràmetre 'order' invàlid. Valors permesos: {', '.join(valid_orders)}"
        }, status=400)
    
    root_comments = Comment.objects.filter(post=post, parent__isnull=True)
    
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
        summary="Crea un comentari nou",
        request=CommentCreateSerializer,
        responses={
            201: CommentSerializer,
            400: OpenApiResponse(
                description="Dades invàlides",
                examples=[
                    OpenApiExample(
                        'Camp obligatori buit',
                        value={"detail": {"content": ["Aquest camp és obligatori"]}},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Comentari pare no vàlid',
                        value={"detail": "El comentari pare no pertany a aquest post"},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Contingut massa llarg',
                        value={"detail": {"content": ["Assegureu-vos que aquest camp no tingui més de 5000 caràcters"]}},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat o clau invàlida",
                examples=[
                    OpenApiExample(
                        'Sense clau API',
                        value={"detail": "Cal proporcionar una clau API"},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Clau invàlida',
                        value={"detail": "Clau API no vàlida"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Post o comentari pare no trobat",
                examples=[
                    OpenApiExample(
                        'Post inexistent',
                        value={"detail": "Post no trobat"},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Parent inexistent',
                        value={"detail": "Comentari pare no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Crea un comentari (suporta parent_id per respostes i imatge opcional)",
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
            try:
                parent_comment = Comment.objects.get(pk=parent_id, post=post)
            except Comment.DoesNotExist:
                return Response(
                    {"detail": "El comentari pare no pertany a aquest post"},
                    status=400
                )

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
        summary="Edita un comentari existent",
        request=CommentEditSerializer,
        responses={
            200: CommentSerializer,
            400: OpenApiResponse(
                description="Dades invàlides",
                examples=[
                    OpenApiExample(
                        'Contingut massa llarg',
                        value={"detail": {"content": ["Assegureu-vos que aquest camp no tingui més de 5000 caràcters"]}},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat o clau invàlida",
                examples=[
                    OpenApiExample(
                        'Sense clau API',
                        value={"detail": "Cal proporcionar una clau API"},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Clau invàlida',
                        value={"detail": "Clau API no vàlida"},
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Sense permís",
                examples=[
                    OpenApiExample(
                        'No és l\'autor',
                        value={"detail": "No tens permís per editar aquest comentari"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Comentari no trobat",
                examples=[
                    OpenApiExample(
                        'Comentari inexistent',
                        value={"detail": "Comentari no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Edita un comentari (només l'autor)",
        tags=["Comments"],
    )
    def put(self, request, comment_id):
        comment = self.get_object(comment_id)
        if comment.author != request.user:
            return Response(
                {"detail": "No tens permís per editar aquest comentari"}, status=403
            )
        serializer = CommentEditSerializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CommentSerializer(comment).data, status=200)


class DeleteCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Elimina un comentari",
        responses={
            204: OpenApiResponse(description="Comentari eliminat correctament"),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Sense permís",
                examples=[
                    OpenApiExample(
                        'No és l\'autor',
                        value={"detail": "No tens permís per eliminar aquest comentari"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Comentari no trobat",
                examples=[
                    OpenApiExample(
                        'Comentari inexistent',
                        value={"detail": "Comentari no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Elimina un comentari (només l'autor)",
        tags=['Comments']
    )
    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author != request.user:
            return Response(
                {"detail": "No tens permís per eliminar aquest comentari"},
                status=403
            )
        comment.delete()
        return Response({"detail": "Comentari eliminat correctament"}, status=204)


class UpvoteCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dóna un upvote al comentari",
        responses={
            200: OpenApiResponse(
                description="Vots actualitzats",
                examples=[
                    OpenApiExample(
                        'Upvote correcte',
                        value={"votes": 42},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat o clau invàlida",
                examples=[
                    OpenApiExample(
                        'Sense clau API',
                        value={"detail": "Cal proporcionar una clau API"},
                        response_only=True
                    ),
                    OpenApiExample(
                        'Clau invàlida',
                        value={"detail": "Clau API no vàlida"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Comentari no trobat",
                examples=[
                    OpenApiExample(
                        'Comentari inexistent',
                        value={"detail": "Comentari no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Dóna un upvote al comentari",
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
        else:
            # quitar voto (toggle off)
            vote_obj.vote = 0
            vote_obj.save()
            comment.votes -= 1
            comment.save()
        return Response({"votes": comment.votes})


class DownvoteCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dóna un downvote al comentari",
        responses={
            200: OpenApiResponse(
                description="Vots actualitzats",
                examples=[
                    OpenApiExample(
                        'Downvote correcte',
                        value={"votes": -5},
                        response_only=True
                    )
                ]
            ),
            401: OpenApiResponse(
                description="No autenticat",
                examples=[
                    OpenApiExample(
                        'Sense autenticació',
                        value={"detail": "Les credencials d'autenticació no es van proporcionar"},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Comentari no trobat",
                examples=[
                    OpenApiExample(
                        'Comentari inexistent',
                        value={"detail": "Comentari no trobat"},
                        response_only=True
                    )
                ]
            )
        },
        description="Dóna un downvote al comentari",
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
        else:
            # quitar voto (toggle off)
            vote_obj.vote = 0
            vote_obj.save()
            comment.votes += 1
        return Response({"votes": comment.votes})


# -------------------- SEARCH --------------------

@extend_schema(
    summary="Cerca posts i comentaris",
    description=(
        "Cerca posts per títol i comentaris per contingut.\n"
        "\n"
        "Resultats ordenats per data (més recents primer)"
    ),
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Text a cercar",
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
            description="Resultats trobats",
            examples=[
                OpenApiExample(
                    'Cerca exitosa',
                    value={
                        "query": "python",
                        "type": "both",
                        "posts": [],
                        "comments": []
                    },
                    response_only=True
                )
            ]
        ),
        400: OpenApiResponse(
            description='Paràmetres invàlids',
            examples=[
                OpenApiExample(
                    'Query buit',
                    value={"detail": "Cal especificar el paràmetre q"},
                    response_only=True
                ),
                OpenApiExample(
                    'Type invàlid',
                    value={"detail": "El paràmetre type ha de ser 'posts', 'comments' o 'both'"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Search']
)
@api_view(['GET'])
def search_posts_comments(request):
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'both').lower()

    if not query:
        return Response({"detail": "Cal especificar el paràmetre q"}, status=400)

    if search_type not in ['posts', 'comments', 'both']:
        return Response(
            {"detail": "El paràmetre type ha de ser 'posts', 'comments' o 'both'"}, 
            status=400
        )

    result = {}
    if search_type in ['posts', 'both']:
        posts = Post.objects.prefetch_related('communities').filter(title__icontains=query).order_by('-published_date')
        result['posts'] = PostSerializer(posts, many=True).data
    if search_type in ['comments', 'both']:
        comments = Comment.objects.filter(content__icontains=query).order_by('-published_date')
        result['comments'] = CommentSerializer(comments, many=True).data

    return Response({"query": query, "type": search_type, **result})