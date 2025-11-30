from django.urls import path
from .api_views import (MeAPIView, MyPostsAPIView, MyCommentsAPIView,
                        MySavedPostsAPIView, MySavedCommentsAPIView, ToggleSavedPostAPIView, ToggleSavedCommentAPIView) # noqa E501

app_name = "accounts_api"

urlpatterns = [
    path("users/me/", MeAPIView.as_view(), name="me"),
    path("users/me/posts/", MyPostsAPIView.as_view(), name="my_posts"),
    path("users/me/comments/", MyCommentsAPIView.as_view(),
         name="my_comments"),
    path("users/me/saved-posts/", MySavedPostsAPIView.as_view(),
         name="my_saved_posts"),
    path("users/me/saved-comments/", MySavedCommentsAPIView.as_view(),
         name="my_saved_comments"),
    path('api/posts/<int:post_id>/toggle_saved/',
         ToggleSavedPostAPIView.as_view(),
         name='api_toggle_saved_post'),
    path('api/comments/<int:comment_id>/toggle_saved/',
         ToggleSavedCommentAPIView.as_view(),
         name='api_toggle_saved_comment'),
]
