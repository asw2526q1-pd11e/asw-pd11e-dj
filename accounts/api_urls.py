from django.urls import path
from .api_views import MeAPIView, MyPostsAPIView, MyCommentsAPIView

app_name = "accounts_api"

urlpatterns = [
    path("users/me/", MeAPIView.as_view(), name="me"),
    path("users/me/posts/", MyPostsAPIView.as_view(), name="my_posts"),
    path("users/me/comments/", MyCommentsAPIView.as_view(),
         name="my_comments"),
]
