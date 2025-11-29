from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema

from accounts.models import Profile
from accounts.authentication import APIKeyAuthentication
from .serializers import ProfileSerializer
from blog.models import Post, Comment
from blog.serializers import (PostSerializer,
                              CommentSerializer, SavedPostSerializer)
from django.shortcuts import get_object_or_404


class MeAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, user):
        return Profile.objects.get(user=user)

    @swagger_auto_schema(responses={200: ProfileSerializer})
    def get(self, request):
        profile = self.get_object(request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=ProfileSerializer,
        responses={200: ProfileSerializer},
        consumes=['multipart/form-data'],
    )
    def put(self, request):
        profile = self.get_object(request.user)
        serializer = ProfileSerializer(profile,
                                       data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyPostsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = Post.objects.filter(author=request.user)
        if not posts.exists():
            return Response({"detail": "Este usuario no ha "
                                       "publicado nada."},
                            status=status.HTTP_200_OK)
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class MyCommentsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comments = Comment.objects.filter(author=request.user)
        if not comments.exists():
            return Response({"detail": "Este usuario no ha comentado nada."},
                            status=status.HTTP_200_OK)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class MySavedPostsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved_posts = request.user.profile.saved_posts.all()

        if not saved_posts.exists():
            return Response({"detail": "No hay posts guardados."},
                            status=status.HTTP_200_OK)

        serializer = SavedPostSerializer(saved_posts, many=True)
        return Response(serializer.data)


class MySavedCommentsAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        saved_comments = profile.saved_comments.all()

        if not saved_comments.exists():
            return Response({"detail": "No hay comentarios guardados."})

        serializer = CommentSerializer(saved_comments, many=True)
        return Response(serializer.data)


class ToggleSavedPostAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        profile = request.user.profile

        if post in profile.saved_posts.all():
            profile.saved_posts.remove(post)
            saved = False
        else:
            profile.saved_posts.add(post)
            saved = True

        return Response({"saved": saved})


class ToggleSavedCommentAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        profile = request.user.profile

        if comment in profile.saved_comments.all():
            profile.saved_comments.remove(comment)
            saved = False
        else:
            profile.saved_comments.add(comment)
            saved = True

        return Response({"saved": saved})