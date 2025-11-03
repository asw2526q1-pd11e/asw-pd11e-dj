from django.urls import path
from . import views

urlpatterns = [
    path("", views.community_list, name="community_list"),
    path("create/", views.community_create, name="community_create"),
    path('<int:pk>/', views.community_site, name='community_site'),
]
