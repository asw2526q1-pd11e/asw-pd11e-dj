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
    path('api/communities/create/',
         api_views.CommunityCreateAPIView.as_view(),
         name='community-create'),
    path('api/communities/<int:pk>/subscribe/',
         api_views.community_subscribe_api,
         name='subscribe-community'),
    path('api/communities/<int:pk>/unsubscribe/',
         api_views.community_unsubscribe_api,
         name='unsubscribe-community'),
    path('api/communities/filter',
         api_views.communities_list_filtered,
         name='communities_filtered'),
]
