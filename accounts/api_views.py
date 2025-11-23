from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from accounts.models import Profile
from .serializers import ProfileSerializer
from accounts.authentication import APIKeyAuthentication


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
