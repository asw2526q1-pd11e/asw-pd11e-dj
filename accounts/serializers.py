from rest_framework import serializers
from accounts.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "nombre",
            "bio",
            "avatar",
            "banner",
            "api_key",
        ]
