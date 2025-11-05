from django.urls import path
from .views import post_views

app_name = "blog"

urlpatterns = [
    path("", post_views.post_list, name="post_list"),
    path("create/", post_views.post_create, name="post_create"),
]
