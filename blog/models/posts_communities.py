from django.db import models


class PostsCommunities(models.Model):
    post = models.ForeignKey("blog.Post", on_delete=models.CASCADE)
    community = models.ForeignKey("communities.Community", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("post", "community")
        verbose_name_plural = "Posts Communities"

    def __str__(self):
        return f"{self.post.title} ↔ {self.community.name}"
