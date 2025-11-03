from django.db import models


class Community(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to="community_avatars/",
                               blank=True,
                               null=True)
    banner = models.ImageField(upload_to="community_banners/",
                               blank=True,
                               null=True)

    def __str__(self):
        return self.name or f"Comunitat #{self.id}"
