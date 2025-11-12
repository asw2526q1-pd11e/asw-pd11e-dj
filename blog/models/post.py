import uuid
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from django.urls import reverse
from PIL import Image
from django.contrib.auth.models import User


def post_image_path(instance, filename):
    """
    Returns S3 path: posts/<username>/<uuid>.webp
    S3 will create the "folders" automatically, no need to pre-create them.
    """
    return f"posts/{instance.author.username}/{uuid.uuid4()}.webp"


class Post(models.Model):
    title = models.CharField(max_length=200, blank=False, null=False)
    content = models.TextField(max_length=5000, blank=False, null=False)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
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
        # Convert uploaded image to WebP
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
                print(f"⚠️ Error converting image to WebP: {e}")

        # Ensure URL is set
        if not self.url:
            super().save(*args, **kwargs)
            self.url = self.get_absolute_url()
            super().save(update_fields=["url"])
        else:
            super().save(*args, **kwargs)
