from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotAuthenticated
from drf_spectacular.utils import (extend_schema,
                                   OpenApiResponse, OpenApiExample)

from accounts.models import Profile
from django.contrib.auth.models import User
from accounts.authentication import APIKeyAuthentication
from .serializers import ProfileSerializer
from blog.models import Post, Comment
from blog.serializers import (PostSerializer,
                              CommentSerializer, SavedPostSerializer)


class CustomIsAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        if (not request.user or not request.user.is_authenticated):
            raise NotAuthenticated(detail="No has iniciat sessió "
                                          "o credencials invàlides")
        return True


class MeAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Obtenir perfil de l'usuari",
        description=(
                "Retorna la informació completa "
                "del perfil de l'usuari autenticat.\n"
                "\n"
                "**Informació retornada:**\n"
                "- Nom d'usuari\n"
                "- Biografia\n"
                "- Foto de perfil\n"
                "- Banner de perfil\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida i activa"
        ),
        responses={
            200: ProfileSerializer,
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Perfil no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Actualitzar perfil de l'usuari",
        description=(
                "Actualitza la informació del perfil de l'usuari autenticat.\n"
                "\n"
                "**Camps modificables:**\n"
                "- Nom de l'usuari\n"
                "- Biografia\n"
                "- Foto de perfil\n"
                "- Banner del perfil\n"
                "\n"
                "**Característiques:**\n"
                "- Els camps no enviats mantenen el seu valor actual\n"
                "- Validació automàtica de les dades\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        request=ProfileSerializer,
        responses={
            200: ProfileSerializer,
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per actualitzar aquest perfil"},
                    response_only=True
                )]
            ),
        }
    )
    def put(self, request):
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Perfil no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileSerializer(profile,
                                       data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyPostsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir posts de l'usuari",
        description=(
                "Retorna tots els posts publicats per l'usuari autenticat.\n"
                "\n"
                "**Informació inclosa per cada post:**\n"
                "- Títol i contingut complet\n"
                "- Imatges\n"
                "- Data de creació\n"
                "- Nombre de m'agrada\n"
                "- Autor\n"
                "- Comunitat a la que pertany\n"
                "- Url continguda\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: PostSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha posts",
                examples=[OpenApiExample(
                    "NoPosts",
                    value={"error": "Aquest usuari no ha publicat res"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request):
        posts = Post.objects.filter(author=request.user)
        if not posts.exists():
            return Response(
                {"error": "Aquest usuari no ha publicat res"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyCommentsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir comentaris de l'usuari",
        description=(
                "Retorna tots els comentaris "
                "escrits per l'usuari autenticat.\n"
                "\n"
                "**Informació inclosa per cada comentari:**\n"
                "- Contingut del comentari\n"
                "- Data de publicació\n"
                "- Referència al post original\n"
                "- Nombre de m'agrada rebuts\n"
                "- Url i imatge\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: CommentSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha comentaris",
                examples=[OpenApiExample(
                    "NoComments",
                    value={"error": "Aquest usuari no ha comentat res"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request):
        comments = Comment.objects.filter(author=request.user)
        if not comments.exists():
            return Response(
                {"error": "Aquest usuari no ha comentat res"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MySavedPostsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir posts guardats",
        description=(
                "Retorna tots els posts guardats a "
                "la col·lecció personal de l'usuari.\n"
                "\n"
                "**Informació inclosa per cada post:**\n"
                "- Títol i contingut complet\n"
                "- Imatges\n"
                "- Data de creació\n"
                "- Nombre de m'agrada\n"
                "- Autor\n"
                "- Comunitat a la que pertany\n"
                "- Url continguda\n"
                "\n"
                "**Característiques:**\n"
                "- Els posts es mantenen fins que l'usuari els elimini\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: SavedPostSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha posts guardats",
                examples=[OpenApiExample(
                    "NoSavedPosts",
                    value={"error": "No hi ha posts guardats"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"error": "Perfil no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        saved_posts = profile.saved_posts.all()
        if not saved_posts.exists():
            return Response(
                {"error": "No hi ha posts guardats"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SavedPostSerializer(saved_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MySavedCommentsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir comentaris guardats",
        description=(
                "Retorna tots els comentaris guardats a "
                "la col·lecció personal de l'usuari.\n"
                "\n"
                "**Informació inclosa per cada comentari:**\n"
                "- Contingut del comentari\n"
                "- Data de publicació\n"
                "- Referència al post original\n"
                "- Nombre de m'agrada rebuts\n"
                "- Url i imatge\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: CommentSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha comentaris guardats",
                examples=[OpenApiExample(
                    "NoSavedComments",
                    value={"error": "No hi ha comentaris guardats"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"error": "Perfil no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        saved_comments = profile.saved_comments.all()
        if not saved_comments.exists():
            return Response(
                {"error": "No hi ha comentaris guardats"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentSerializer(saved_comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ToggleSavedPostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Guardar o treure post de guardats",
        description=(
                "Alterna l'estat de guardat d'un post.\n"
                "\n"
                "**Comportament:**\n"
                "- Si el post està guardat → l'elimina de guardats\n"
                "- Si el post NO està guardat → l'afegeix a guardats\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: OpenApiResponse(
                description="Estat del post guardat",
                examples=[OpenApiExample(
                    "PostToggled",
                    value={"saved": True},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                description="Post no trobat",
                examples=[OpenApiExample(
                    "PostNotFound",
                    value={"error": "No s'ha trobat el post amb aquest ID"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís "
                                    "per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def post(self, request, post_id):
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return Response(
                {"error": "No s'ha trobat el post amb aquest ID"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"error": "Perfil no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        if post in profile.saved_posts.all():
            profile.saved_posts.remove(post)
            saved = False
        else:
            profile.saved_posts.add(post)
            saved = True

        return Response({"saved": saved}, status=status.HTTP_200_OK)


class ToggleSavedCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Guardar o treure comentari de guardats",
        description=(
                "Alterna l'estat de guardat d'un comentari.\n"
                "\n"
                "**Comportament:**\n"
                "- Si el comentari està guardat → l'elimina de guardats\n"
                "- Si el comentari NO està guardat → l'afegeix a guardats\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: OpenApiResponse(
                description="Estat del comentari guardat",
                examples=[OpenApiExample(
                    "CommentToggled",
                    value={"saved": True},
                    response_only=True
                )]
            ),
            404: OpenApiResponse(
                description="Comentari no trobat",
                examples=[OpenApiExample(
                    "CommentNotFound",
                    value={"error": "No s'ha trobat"
                                    " el comentari amb aquest ID"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís per "
                                    "accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def post(self, request, comment_id):
        try:
            comment = Comment.objects.get(pk=comment_id)
        except Comment.DoesNotExist:
            return Response(
                {"error": "No s'ha trobat el comentari amb aquest ID"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response(
                {"error": "Perfil no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        if comment in profile.saved_comments.all():
            profile.saved_comments.remove(comment)
            saved = False
        else:
            profile.saved_comments.add(comment)
            saved = True

        return Response({"saved": saved}, status=status.HTTP_200_OK)

class UserProfileAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir perfil d'un usuari",
        description=(
                "Retorna la informació pública del perfil d'un usuari específic.\n"
                "\n"
                "**Informació retornada:**\n"
                "- Nom d'usuari\n"
                "- Nom\n"
                "- Biografia\n"
                "- Foto de perfil\n"
                "- Banner de perfil\n"
                "\n"
                "**Nota:** L'API Key no es retorna per seguretat\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida i activa"
        ),
        responses={
            200: ProfileSerializer,
            404: OpenApiResponse(
                description="Usuari no trobat",
                examples=[OpenApiExample(
                    "UserNotFound",
                    value={"error": "Usuari no trobat"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request, user_id):
        try:
            profile = Profile.objects.select_related('user').get(user__id=user_id)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Usuari no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileSerializer(profile)
        data = serializer.data

        data.pop('api_key', None)

        return Response(data, status=status.HTTP_200_OK)

class UserPostsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir posts d'un usuari específic",
        description=(
                "Retorna tots els posts publicats per un usuari específic.\n"
                "\n"
                "**Informació inclosa per cada post:**\n"
                "- Títol i contingut complet\n"
                "- Imatges\n"
                "- Data de creació\n"
                "- Nombre de m'agrada\n"
                "- Autor\n"
                "- Comunitat a la que pertany\n"
                "- Url continguda\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: PostSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha posts",
                examples=[OpenApiExample(
                    "NoPosts",
                    value={"error": "Aquest usuari no ha publicat res"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request, user_id):
        from django.contrib.auth.models import User

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuari no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        posts = Post.objects.filter(author=user)
        if not posts.exists():
            return Response(
                {"error": "Aquest usuari no ha publicat res"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserCommentsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir comentaris d'un usuari específic",
        description=(
                "Retorna tots els comentaris escrits per un usuari específic.\n"
                "\n"
                "**Informació inclosa per cada comentari:**\n"
                "- Contingut del comentari\n"
                "- Data de publicació\n"
                "- Referència al post original\n"
                "- Nombre de m'agrada rebuts\n"
                "- Url i imatge\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: CommentSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha comentaris",
                examples=[OpenApiExample(
                    "NoComments",
                    value={"error": "Aquest usuari no ha comentat res"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuari no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        comments = Comment.objects.filter(author=user)
        if not comments.exists():
            return Response(
                {"error": "Aquest usuari no ha comentat res"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserSavedPostsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir posts guardats d'un usuari específic",
        description=(
                "Retorna tots els posts guardats per un usuari específic.\n"
                "\n"
                "**Informació inclosa per cada post:**\n"
                "- Títol i contingut complet\n"
                "- Imatges\n"
                "- Data de creació\n"
                "- Nombre de m'agrada\n"
                "- Autor\n"
                "- Comunitat a la que pertany\n"
                "- Url continguda\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: SavedPostSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha posts guardats",
                examples=[OpenApiExample(
                    "NoSavedPosts",
                    value={"error": "Aquest usuari no té posts guardats"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request, user_id):
        try:
            profile = Profile.objects.select_related('user').get(user__id=user_id)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Usuari no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        saved_posts = profile.saved_posts.all()
        if not saved_posts.exists():
            return Response(
                {"error": "Aquest usuari no té posts guardats"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SavedPostSerializer(saved_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSavedCommentsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [CustomIsAuthenticated]

    @extend_schema(
        summary="Obtenir comentaris guardats d'un usuari específic",
        description=(
                "Retorna tots els comentaris guardats per un usuari específic.\n"
                "\n"
                "**Informació inclosa per cada comentari:**\n"
                "- Contingut del comentari\n"
                "- Data de publicació\n"
                "- Referència al post original\n"
                "- Nombre de m'agrada rebuts\n"
                "- Url i imatge\n"
                "\n"
                "**Requisits:**\n"
                "- API Key vàlida"
        ),
        responses={
            200: CommentSerializer(many=True),
            404: OpenApiResponse(
                description="No hi ha comentaris guardats",
                examples=[OpenApiExample(
                    "NoSavedComments",
                    value={"error": "Aquest usuari no té comentaris guardats"},
                    response_only=True
                )]
            ),
            403: OpenApiResponse(
                description="No autoritzat",
                examples=[OpenApiExample(
                    "NotAuthorized",
                    value={"error": "No tens permís per accedir a aquest recurs"},
                    response_only=True
                )]
            )
        }
    )
    def get(self, request, user_id):
        try:
            profile = Profile.objects.select_related('user').get(user__id=user_id)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Usuari no trobat"},
                status=status.HTTP_404_NOT_FOUND
            )

        saved_comments = profile.saved_comments.all()
        if not saved_comments.exists():
            return Response(
                {"error": "Aquest usuari no té comentaris guardats"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CommentSerializer(saved_comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)