import uuid
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image


def comment_image_path(instance, filename):
    """Genera un nombre único para cada imagen de comentario."""
    return os.path.join("comment_image", f"{uuid.uuid4()}.webp")


class Comment(models.Model):
    post = models.ForeignKey(
        "blog.Post",
        on_delete=models.CASCADE,
        related_name="comments",
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )

    content = models.TextField(max_length=5000)
    author = models.CharField(max_length=100)
    published_date = models.DateTimeField(default=timezone.now)
    votes = models.IntegerField(default=0)
    url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to=comment_image_path,
                              blank=True, null=True)

    def __str__(self):
        prefix = "↳ Reply" if self.parent else "Comment"
        return f"{prefix} by {self.author}: {self.content[:40]}..."

    @property
    def is_root_comment(self):
        return self.parent is None

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
                print(f"Error al convertir imagen a WebP en Comment: {e}")

        # Solo intentar copiar la URL si realmente hay un post
        if not self.url:
            try:
                if self.post_id:
                    self.url = self.post.url
            except Exception:
                pass

        super().save(*args, **kwargs)

    class Meta:
        ordering = ["published_date"]
