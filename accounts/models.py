from django.db import models
from django.contrib.auth.models import User
from blog.models import Post


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)
    saved_posts = models.ManyToManyField(Post,
                                         blank=True, related_name='saved_by')

    def __str__(self):
        return self.user.username
