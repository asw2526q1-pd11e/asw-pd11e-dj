from django.urls import path
from .api_views import post_list  # aquí posarem més views API més endavant

app_name = "blog_api"

urlpatterns = [
    path('posts/', post_list, name='post_list'),
]
