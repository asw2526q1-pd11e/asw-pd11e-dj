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
    path(
        "posts/<int:post_id>/comments/create/",
        post_views.comment_create,
        name="comment_create",
    ),  # /posts/1/comments/create/
    path(
        "comments/<int:comment_id>/upvote/",
        post_views.comment_upvote,
        name="comment_upvote",
    ),  # /comments/1/upvote/
    path(
        "comments/<int:comment_id>/downvote/",
        post_views.comment_downvote,
        name="comment_downvote",
    ),  # /comments/1/downvote/
    path(
        "comments/<int:comment_id>/delete/",
        post_views.comment_delete,
        name="comment_delete",
    ),  # /comments/1/delete/
    path(
        "comments/<int:comment_id>/edit/",
        post_views.comment_edit,
        name="comment_edit",
    ),  # /comments/1/edit/
    path("posts/<int:pk>/edit/",
         post_views.post_edit,
         name="post_edit"),
    path("search/", post_views.search_view, name="search"),
    path("posts/<int:pk>/delete/", post_views.post_delete, name="post_delete"),
]
