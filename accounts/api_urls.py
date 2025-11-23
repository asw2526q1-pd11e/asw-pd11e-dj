from django.urls import path
from .api_views import MeAPIView

app_name = "accounts_api"

urlpatterns = [
    path("users/me/", MeAPIView.as_view(), name="me"),
]
