from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers, status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from .models import Community
from django.db import models

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


# -------------------- VIEWS --------------------

@swagger_auto_schema(
    method='get',
    operation_description="Retorna la llista de totes les comunitats amb informació bàsica: nom, avatar, banner, número de subscriptors, posts i comentaris.",  # noqa E501
    responses={
        200: CommunitySerializer(many=True),
        500: 'Error intern del servidor'
    }
)
@api_view(['GET'])
def community_list_api(request):
    """
    GET /api/communities/
    Retorna totes les comunitats.
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
    operation_description="Retorna la informació d'una comunitat concreta per id. Inclou número de subscriptors, posts i comentaris.",  # noqa E501
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
    Retorna una comunitat concreta.
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
