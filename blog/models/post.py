import uuid
import os
from django.db import models
from django.utils import timezone
from django.urls import reverse


def post_image_path(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("post_image", filename)


class Post(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    content = models.TextField(max_length=5000, blank=False, null=False)
    author = models.CharField(max_length=100, blank=False, null=False)
    published_date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=0)
    image = models.ImageField(upload_to=post_image_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    communities = models.ManyToManyField(
        "communities.Community", through="blog.PostsCommunities", related_name="posts"
    )

    def __str__(self):
        return f"{self.title} — {self.author}: {self.content[:50]}..."

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[str(self.id)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Guarda primero para obtener el ID
        if not self.url:
            self.url = self.get_absolute_url()
            super().save(update_fields=["url"])
