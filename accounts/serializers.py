from rest_framework import serializers
from accounts.models import Profile


class ErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    nombre = serializers.CharField(required=False,
                                   allow_blank=True, default="")
    bio = serializers.CharField(required=False, allow_blank=True, default="")
    avatar = serializers.ImageField(required=False, allow_null=True)
    banner = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ["username", "nombre", "bio", "avatar", "banner", "api_key"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not rep["nombre"]:
            rep["nombre"] = instance.user.username
        if not rep["bio"]:
            rep["bio"] = "Este usuario no tiene biografía."
        return rep

    def update(self, instance, validated_data):
        for attr in ['nombre', 'bio']:
            value = validated_data.get(attr, None)
            if value is not None:
                if value.strip():
                    setattr(instance, attr, value)
                else:
                    setattr(instance, attr, "")

        for attr in ['avatar', 'banner']:
            if attr in validated_data:
                value = validated_data[attr]
                if value in (None, ""):
                    setattr(instance, attr, None)
                else:
                    setattr(instance, attr, value)

        instance.save()
        return instance
