import uuid
from django.db import models
from django.contrib.auth.models import User
from blog.models import Post, Comment


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    saved_posts = models.ManyToManyField(Post,
                                         blank=True, related_name='saved_by')
    saved_comments = models.ManyToManyField(Comment,
                                            blank=True,
                                            related_name='saved_by_comments')
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.user.username

    def generate_api_key(self):
        self.api_key = uuid.uuid4()
        self.save()
