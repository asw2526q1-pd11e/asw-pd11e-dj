# accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('toggle-saved/<int:post_id>/',
         views.toggle_saved_post, name='toggle_saved_post'),
]
