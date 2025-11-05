from django.db import models
import uuid
import os


def community_avatar_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("community_avatars", filename)


def community_banner_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("community_banners", filename)


class Community(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to=community_avatar_path,
                               blank=True, null=True)
    banner = models.ImageField(upload_to=community_banner_path,
                               blank=True, null=True)

    def __str__(self):
        return self.name or f"Comunitat #{self.id}"
