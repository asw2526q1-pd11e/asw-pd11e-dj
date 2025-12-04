# flake8: noqa
"""
URL configuration for asw_pd11e_dj project.
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# DRF Spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Funció per redirigir la pàgina principal al blog
def redirect_to_blog(request):
    return redirect("blog:post_list")


urlpatterns = [
    # Arrel
    path("", redirect_to_blog),

    # Admin i comptes
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("accounts/", include("allauth.urls")),

    # Blog i comunitats
    path("blog/", include(("blog.urls", "blog"), namespace="blog")),
    path("communities/", include(("communities.urls", "communities"), namespace="communities")),

    # APIs
    path("api/accounts/", include(("accounts.api_urls", "accounts_api"), namespace="accounts_api")),
    path("api/blog/", include(("blog.api_urls", "blog_api"), namespace="blog_api")),
    path("api/communities/", include(("communities.api_urls", "communities_api"), namespace="communities_api")),

    # OpenAPI Schema via Spectacular
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI i Redoc
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
