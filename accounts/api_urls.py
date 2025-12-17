from django.urls import path
from .api_views import (
    MeAPIView, MyPostsAPIView, MyCommentsAPIView,
    MySavedPostsAPIView, MySavedCommentsAPIView,
    ToggleSavedPostAPIView, ToggleSavedCommentAPIView,
    UserProfileAPIView, UserPostsAPIView, UserCommentsAPIView,
    UserSavedPostsAPIView, UserSavedCommentsAPIView
)

app_name = "accounts_api"

urlpatterns = [
    # Endpoints de "me" (usuario autenticado)
    path("users/me/", MeAPIView.as_view(), name="me"),
    path("users/me/posts/",
         MyPostsAPIView.as_view(), name="my_posts"),
    path("users/me/comments/",
         MyCommentsAPIView.as_view(), name="my_comments"),
    path("users/me/saved-posts/",
         MySavedPostsAPIView.as_view(), name="my_saved_posts"),
    path("users/me/saved-comments/",
         MySavedCommentsAPIView.as_view(), name="my_saved_comments"),

    # Endpoints de toggle saved
    path('api/posts/<int:post_id>/toggle_saved/',
         ToggleSavedPostAPIView.as_view(), name='api_toggle_saved_post'),
    path('api/comments/<int:comment_id>/toggle_saved/',
         ToggleSavedCommentAPIView.as_view(), name='api_toggle_saved_comment'),

    # Endpoints de usuarios específicos
    path('users/<int:user_id>/',
         UserProfileAPIView.as_view(), name='user-profile'),
    path('users/<int:user_id>/posts/',
         UserPostsAPIView.as_view(), name='user-posts'),
    path('users/<int:user_id>/comments/',
         UserCommentsAPIView.as_view(), name='user-comments'),
    path('users/<int:user_id>/saved-posts/',
         UserSavedPostsAPIView.as_view(), name='user-saved-posts'),
    path('users/<int:user_id>/saved-comments/',
         UserSavedCommentsAPIView.as_view(), name='user-saved-comments'),
]
