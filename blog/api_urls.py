from django.urls import path
from .api_views import post_detail, post_list

app_name = "blog_api"

urlpatterns = [
    path('posts/', post_list, name='post_list'),
    path('posts/<int:pk>/', post_detail, name='post_detail'),
]
