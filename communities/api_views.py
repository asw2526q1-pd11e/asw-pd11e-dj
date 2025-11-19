# flake8: noqa E501
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers, status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from django.db import models

from blog.models import Post
from communities.models import Community

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