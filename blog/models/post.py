import uuid
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.urls import reverse
from PIL import Image


def post_image_path(instance, filename):
    return os.path.join("post_image", f"{uuid.uuid4()}.webp")


class Post(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    content = models.TextField(max_length=5000, blank=False, null=False)
    author = models.CharField(max_length=100, blank=False, null=False)
    published_date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=0)
    image = models.ImageField(upload_to=post_image_path, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    communities = models.ManyToManyField(
        "communities.Community",
        through="blog.PostsCommunities",
        related_name="posts",
    )

    def __str__(self):
        return f"{self.title} — {self.author}: {self.content[:50]}..."

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[str(self.id)])

    def save(self, *args, **kwargs):
        if self.image and not self.image.name.endswith(".webp"):
            try:
                img = Image.open(self.image).convert("RGB")

                buffer = BytesIO()
                img.save(buffer, format="WEBP", quality=85)
                buffer.seek(0)

                new_name = f"{uuid.uuid4()}.webp"
                self.image.save(new_name,
                                ContentFile(buffer.read()),
                                save=False)
                buffer.close()
            except Exception as e:
                print(f"⚠️ Error al convertir imagen a WebP: {e}")

        if not self.url:
            super().save(*args, **kwargs)
            self.url = self.get_absolute_url()
            super().save(update_fields=["url"])
        else:
            super().save(*args, **kwargs)
