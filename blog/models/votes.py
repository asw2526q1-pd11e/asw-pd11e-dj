from django.db import models
from django.contrib.auth.models import User
from blog.models import Post, Comment

# -------------------- VOTES -------------------- #


class VotePost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="post_votes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="votes_set")
    vote = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user} voted {self.vote} on {self.post}"


class VoteComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="comment_votes")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                related_name="votes_set")
    vote = models.SmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "comment")

    def __str__(self):
        return f"{self.user} voted {self.vote} on comment {self.comment.id}"
