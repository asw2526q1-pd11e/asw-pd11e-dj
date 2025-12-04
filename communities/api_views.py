# flake8: noqa E501
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers, status
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.db import models
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import APIKeyAuthentication
from blog.models import Post
from communities.models import Community
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import authentication_classes, permission_classes
from django.http import Http404

# -------------------- SERIALIZERS --------------------

class CommunitySerializer(serializers.ModelSerializer):
    subs_count = serializers.IntegerField(
        source='subscribers.count',
        read_only=True,
        help_text="Número de subscriptors de la comunitat"
    )
    posts_count = serializers.IntegerField(
        help_text="Número de posts dins la comunitat",
        read_only=True
    )
    comments_count = serializers.IntegerField(
        help_text="Número de comentaris dins la comunitat",
        read_only=True
    )

    class Meta:
        model = Community
        fields = [
            'id',
            'name',
            'avatar',
            'banner',
            'subs_count',
            'posts_count',
            'comments_count'
        ]


class PostSerializer(serializers.ModelSerializer):
    """
    Serializer per posts amb informació de les comunitats.
    Utilitzat en l'endpoint de posts per comunitat.
    """
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
        ref_name = "PostSerializerInCommunities"

class CommunityCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200, help_text="Nom de la comunitat")
    avatar = serializers.ImageField(required=False, allow_null=True)
    banner = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Community
        fields = ['id', 'name', 'avatar', 'banner']
        read_only_fields = ['id']

# -------------------- VIEWS --------------------

@extend_schema(
    summary="Llista de comunitats",
    description=(
        "Retorna la llista de totes les comunitats amb informació bàsica: nom, avatar, banner, número de subscriptors, posts i comentaris.\n"
        "\n"
        "**Paràmetres de filtratge (filter):**\n"
        "- **all** (defecte): Retorna totes les comunitats sense filtre\n"
        "- **subscribed**: Retorna només comunitats a les quals l'usuari està subscrit. **Requereix autenticació**\n"
        "- **local**: Retorna només comunitats a les quals l'usuari NO està subscrit. **Requereix autenticació**\n"
        "\n"
        "**Notes:**\n"
        "- Els filtres 'subscribed' i 'local' retornen un error 401 si l'usuari no està autenticat\n"
        "- Cada comunitat inclou estadístiques agregades de posts i comentaris"
    ),
    parameters=[
        OpenApiParameter(
            name='filter',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Filtre per estat de subscripció (subscribed i local requereixen autenticació)",
            enum=['all', 'subscribed', 'local'],
            default='all',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=CommunitySerializer(many=True),
            description="Llista de comunitats retornada correctament"
        ),
        400: OpenApiResponse(
            description="Bad Request - Paràmetre invàlid",
            examples=[
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
                    value={"error": "Error intern del servidor"},
                    response_only=True
                )
            ]
        )
    },
    tags=['Communities']
)
@api_view(['GET'])
def community_list_api(request):
    """
    GET /api/communities/?filter=all
    Retorna totes les comunitats amb estadístiques agregades i filtratge per subscripció.
    """
    try:
        # Obtenir paràmetre de filtratge
        filter_type = request.GET.get('filter', 'all').lower()
        
        # Validar paràmetre
        valid_filters = ['all', 'subscribed', 'local']
        if filter_type not in valid_filters:
            return Response({
                "error": f"Paràmetre 'filter' invàlid. Valors permesos: {', '.join(valid_filters)}"
            }, status=400)
        
        # Filtres subscribed i local requereixen autenticació
        if filter_type in ['subscribed', 'local'] and not request.user.is_authenticated:
            return Response({
                "error": "Cal autenticació per utilitzar els filtres 'subscribed' o 'local'"
            }, status=401)
        
        # Obtenir comunitats amb anotacions
        communities = Community.objects.annotate(
            posts_count=models.Count('posts', distinct=True),
            comments_count=models.Count('posts__comments', distinct=True)
        )
        
        # Aplicar filtre
        if filter_type == 'subscribed' and request.user.is_authenticated:
            # Comunitats a les quals l'usuari està subscrit
            communities = communities.filter(subscribers=request.user)
        
        elif filter_type == 'local' and request.user.is_authenticated:
            # Comunitats a les quals l'usuari NO està subscrit
            communities = communities.exclude(subscribers=request.user)
        
        # Retornar missatge si no hi ha comunitats
        if not communities.exists():
            return Response({
                "message": "No s'han trobat comunitats amb els filtres aplicats",
                "communities": []
            }, status=status.HTTP_200_OK)
        
        serializer = CommunitySerializer(communities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error intern del servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Detall d'una comunitat",
    description="Retorna la informació d'una comunitat concreta per id. Inclou número de subscriptors, posts i comentaris",
    responses={
        200: CommunitySerializer,
        404: OpenApiResponse(description='Comunitat no trobada'),
        500: OpenApiResponse(description='Error intern del servidor')
    },
    tags=['Communities']
)
@api_view(['GET'])
def community_detail_api(request, pk):
    """
    GET /api/communities/{id}/
    Retorna una comunitat concreta amb estadístiques.
    """
    try:
        community = get_object_or_404(
            Community.objects.annotate(
                posts_count=models.Count('posts', distinct=True),
                comments_count=models.Count('posts__comments', distinct=True)
            ),
            pk=pk
        )
        serializer = CommunitySerializer(community)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Http404:
        return Response(
            {"detail": "Comunitat no trobada"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Error intern del servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(
    summary="Posts d'una comunitat",
    description="Retorna tots els posts d'una comunitat concreta amb tota la informació del post, incloent totes les comunitats a les quals pertanyen (no només la comunitat filtrada). Els posts s'ordenen per data de publicació (més recents primer)",
    responses={
        200: PostSerializer(many=True),
        404: OpenApiResponse(description='Comunitat no trobada'),
        500: OpenApiResponse(description='Error intern del servidor')
    },
    tags=['Communities']
)
@api_view(['GET'])
def community_posts_api(request, pk):
    """
    GET /api/communities/{id}/posts/
    Retorna tots els posts d'una comunitat ordenats per data (més recents primer).
    Cada post inclou la llista de totes les comunitats a les quals pertany.
    """
    try:
        community = get_object_or_404(Community, pk=pk)
        posts = Post.objects.prefetch_related('communities').filter(
            communities=community
        ).order_by('-published_date')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Http404:
        return Response(
            {"detail": "Comunitat no trobada"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Error intern del servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class CommunityCreateAPIView(generics.CreateAPIView):
    """
    API endpoint per crear una comunitat nova.
    Permite subir avatar y banner.
    """
    serializer_class = CommunityCreateSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Crear comunitat",
        description=(
            "Crea una comunitat nova amb:\n"
            "- **name**: Nom de la comunitat (obligatori)\n"
            "- **avatar**: Imatge d'avatar (opcional)\n"
            "- **banner**: Imatge de banner (opcional)\n"
            "\n"
            "L'usuari autenticat es converteix automàticament en el primer subscriptor."
        ),
        request=CommunityCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=CommunitySerializer,
                description="Comunitat creada correctament"
            ),
            400: OpenApiResponse(description="Dades invàlides"),
            401: OpenApiResponse(description="No autenticat")
        },
        tags=['Communities']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        community = serializer.save()

        if self.request.user.is_authenticated:
            community.subscribers.add(self.request.user)
            community.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        community = serializer.instance

        annotated_community = Community.objects.annotate(
            posts_count=models.Count('posts', distinct=True),
            comments_count=models.Count('posts__comments', distinct=True)
        ).get(pk=community.pk)

        output_serializer = CommunitySerializer(annotated_community)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

@extend_schema(
    summary="Subscriure's a una comunitat",
    description="Subscriu l'usuari autenticat a una comunitat",
    responses={
        200: OpenApiResponse(
            description="Subscripció realitzada correctament",
            examples=[
                OpenApiExample(
                    'Subscripció correcta',
                    value={"message": "Subscripció realitzada correctament"},
                    response_only=True
                )
            ]
        ),
        400: OpenApiResponse(
            description="L'usuari ja està subscrit",
            examples=[
                OpenApiExample(
                    'Ja subscrit',
                    value={"error": "Ja estàs subscrit a aquesta comunitat"},
                    response_only=True
                )
            ]
        ),
        401: OpenApiResponse(description="No autenticat"),
        404: OpenApiResponse(description="Comunitat no trobada")
    },
    tags=["Communities"]
)
@api_view(['POST'])
def community_subscribe_api(request, pk):
    """
    POST /api/communities/{id}/subscribe/
    Suscribe al usuario autenticado a una comunidad.
    """
    if not request.user.is_authenticated:
        return Response(
            {"error": "Usuari no autenticat"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        community = get_object_or_404(Community, pk=pk)
    except Http404:
        return Response(
            {"detail": "Comunitat no trobada"},
            status=status.HTTP_404_NOT_FOUND,
        )
    if request.user in community.subscribers.all():
        return Response(
            {"error": "Ja estàs subscrit a aquesta comunitat"},
            status=status.HTTP_400_BAD_REQUEST
        )

    community.subscribers.add(request.user)
    return Response(
        {"message": "Subscripció realitzada correctament"},
        status=status.HTTP_200_OK
    )

@extend_schema(
    summary="Donar-se de baixa d'una comunitat",
    description="Elimina l'usuari autenticat de la llista de subscriptors d'una comunitat",
    responses={
        200: OpenApiResponse(
            description="Baixa realitzada correctament",
            examples=[
                OpenApiExample(
                    'Baixa correcta',
                    value={"message": "T'has donat de baixa correctament"},
                    response_only=True
                )
            ]
        ),
        400: OpenApiResponse(
            description="L'usuari no estava subscrit",
            examples=[
                OpenApiExample(
                    'No subscrit',
                    value={"error": "No estàs subscrit a aquesta comunitat"},
                    response_only=True
                )
            ]
        ),
        401: OpenApiResponse(description="No autenticat"),
        404: OpenApiResponse(description="Comunitat no trobada")
    },
    tags=["Communities"]
)
@api_view(['POST'])
def community_unsubscribe_api(request, pk):
    """
    POST /api/communities/{id}/unsubscribe/
    elimina al usuario autenticado de la comunidad.
    """
    if not request.user.is_authenticated:
        return Response(
            {"error": "Usuari no autenticat"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        community = get_object_or_404(Community, pk=pk)
    except Http404:
        return Response(
            {"detail": "Comunitat no trobada"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.user not in community.subscribers.all():
        return Response(
            {"error": "No estàs subscrit a aquesta comunitat"},
            status=status.HTTP_400_BAD_REQUEST
        )

    community.subscribers.remove(request.user)
    return Response(
        {"message": "T'has donat de baixa correctament"},
        status=status.HTTP_200_OK
    )