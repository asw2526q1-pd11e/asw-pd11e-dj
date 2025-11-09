from django.urls import path
from .views import post_views

app_name = "blog"

urlpatterns = [
    path(
        "posts/",
        post_views.post_list,
        name="post_list",
    ),  # /posts/
    path(
        "posts/create/",
        post_views.post_create,
        name="post_create",
    ),  # /posts/create/
    path(
        "posts/<int:pk>/",
        post_views.post_detail,
        name="post_detail",
    ),  # /posts/1/
    path(
        "posts/<int:pk>/upvote/",
        post_views.upvote_post,
        name="upvote_post",
    ),  # /posts/1/upvote/
    path(
        "posts/<int:pk>/downvote/",
        post_views.downvote_post,
        name="downvote_post",
    ),  # /posts/1/downvote/
    path(
        "posts/<int:post_id>/comments/",
        post_views.comments_index,
        name="comments_index",
    ),  # /posts/1/comments/
]
