# flake8: noqa E501
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers, status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from django.db import models
from rest_framework.permissions import IsAuthenticated
from accounts.authentication import APIKeyAuthentication
from blog.models import Post
from communities.models import Community
from drf_yasg import openapi
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import authentication_classes, permission_classes

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

@swagger_auto_schema(
    method='get',
    operation_description="Retorna la llista de totes les comunitats amb informació bàsica: nom, avatar, banner, número de subscriptors, posts i comentaris",
    responses={
        200: CommunitySerializer(many=True),
        500: 'Error intern del servidor'
    }
)
@api_view(['GET'])
def community_list_api(request):
    """
    GET /api/communities/
    Retorna totes les comunitats amb estadístiques agregades.
    """
    try:
        communities = Community.objects.annotate(
            posts_count=models.Count('posts', distinct=True),
            comments_count=models.Count('posts__comments', distinct=True)
        )
        serializer = CommunitySerializer(communities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": f"Error intern del servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Retorna la informació d'una comunitat concreta per id. Inclou número de subscriptors, posts i comentaris",
    responses={
        200: CommunitySerializer,
        404: 'Comunitat no trobada',
        500: 'Error intern del servidor'
    }
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
    except Community.DoesNotExist:
        return Response(
            {"error": "Comunitat no trobada"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Error intern del servidor: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Retorna tots els posts d'una comunitat concreta amb tota la informació del post, incloent totes les comunitats a les quals pertanyen (no només la comunitat filtrada)",
    responses={
        200: PostSerializer(many=True),
        404: 'Comunitat no trobada',
        500: 'Error intern del servidor'
    }
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
    except Community.DoesNotExist:
        return Response(
            {"error": "Comunitat no trobada"},
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

    @swagger_auto_schema(
        operation_description="""
        Crea una comunitat nova amb:
        - **name**: Nom de la comunitat (obligatori)
        - **avatar**: Imatge (opcional)
        - **banner**: Imatge (opcional)

        L'usuari autenticat es converteix automàticament en el primer subscriptor.
        """,
        manual_parameters=[
            openapi.Parameter(
                'avatar',
                openapi.IN_FORM,
                description="Imatge d'avatar",
                type=openapi.TYPE_FILE,
                required=False
            ),
            openapi.Parameter(
                'banner',
                openapi.IN_FORM,
                description="Imatge de banner",
                type=openapi.TYPE_FILE,
                required=False
            )
        ],
        consumes=['multipart/form-data'],
        responses={
            201: openapi.Response(
                description="Comunitat creada correctament",
                schema=CommunitySerializer
            ),
            400: "Dades invàlides",
            401: "No autenticat"
        },
        tags=['communities']
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

@swagger_auto_schema(
    method='post',
    operation_description="Subscribirse a una comunidad",
    responses={
        200: "Suscripción realizada correctamente",
        400: "El usuario ya está suscrito",
        401: "No autenticado",
        404: "Comunidad no encontrada"
    },
    tags=["communities"]
)
@api_view(['POST'])
def community_subscribe_api(request, pk):
    """
    POST /api/communities/{id}/subscribe/
    Suscribe al usuario autenticado a una comunidad.
    """
    if not request.user.is_authenticated:
        return Response(
            {"error": "Usuario no autenticado"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    community = get_object_or_404(Community, pk=pk)

    if request.user in community.subscribers.all():
        return Response(
            {"error": "Ya estás suscrito a esta comunidad"},
            status=status.HTTP_400_BAD_REQUEST
        )

    community.subscribers.add(request.user)
    return Response(
        {"message": "Suscripción realizada correctamente"},
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method='post',
    operation_description="Darse de baja de una comunidad",
    responses={
        200: "Te has dado de baja correctamente",
        400: "El usuario no estaba suscrito",
        401: "No autenticado",
        404: "Comunidad no encontrada"
    },
    tags=["communities"]
)
@api_view(['POST'])
def community_unsubscribe_api(request, pk):
    """
    POST /api/communities/{id}/unsubscribe/
    elimina al usuario autenticado de la comunidad.
    """
    if not request.user.is_authenticated:
        return Response(
            {"error": "Usuario no autenticado"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    community = get_object_or_404(Community, pk=pk)

    if request.user not in community.subscribers.all():
        return Response(
            {"error": "No estás suscrito a esta comunidad"},
            status=status.HTTP_400_BAD_REQUEST
        )

    community.subscribers.remove(request.user)
    return Response(
        {"message": "Te has dado de baja correctamente"},
        status=status.HTTP_200_OK
    )
