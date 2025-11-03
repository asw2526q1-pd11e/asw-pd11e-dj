# blog/models.py
from django.db import models
from django.utils import timezone

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.CharField(max_length=100)
    published_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} — {self.author}: {self.content[:50]}..."
