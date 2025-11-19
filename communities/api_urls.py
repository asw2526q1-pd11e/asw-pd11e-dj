from django.urls import path
from . import api_views

app_name = "communities_api"

urlpatterns = [
    path('communities/', api_views.community_list_api, name='community_list'),
    path(
        'communities/<int:pk>/',
        api_views.community_detail_api,
        name='community_detail'
    ),
    path(
        'communities/<int:pk>/posts/',
        api_views.community_posts_api,
        name='community_posts'
    ),
]
