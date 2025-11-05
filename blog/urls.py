from django.urls import path
from .views import post_views

app_name = "blog"

urlpatterns = [
    path("posts/", post_views.post_list, name="post_list"),  # /posts/
    path(
        "posts/create/",
        post_views.post_create,
        name="post_create",
    ),
    path(
        "posts/<int:pk>/",
        post_views.post_detail,
        name="post_detail",
    ),
    path("posts/<int:pk>/upvote/", post_views.upvote_post, name="upvote_post"),
    path("posts/<int:pk>/downvote/",
         post_views.downvote_post,
         name="downvote_post"),
]
