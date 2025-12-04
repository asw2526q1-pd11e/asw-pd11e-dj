"""
URL configuration for asw_pd11e_dj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_spectacular.views import SpectacularAPIView


schema_view = get_schema_view(
    openapi.Info(
        title="Blog API",
        default_version='v1',
        description="Documentació API del Blog",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url="https://asw-pd11e-dj.onrender.com",  # ✅ dominio público
)


# función para redirigir la raíz al listado de posts en el namespace 'blog'
def redirect_to_blog(request):
    return redirect("blog:post_list")


urlpatterns = [
    path("", redirect_to_blog),
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls",
                               "accounts"), namespace="accounts")),
    path("accounts/", include('allauth.urls')),
    path("blog/", include(("blog.urls", "blog"), namespace="blog")),
    path("communities/", include(("communities.urls",
                                  "communities"), namespace="communities")),

    # APIs
    path("api/accounts/", include(("accounts.api_urls",
                                   "accounts_api"), namespace="accounts_api")),
    path("api/blog/", include(("blog.api_urls",
                               "blog_api"), namespace="blog_api")),
    path("api/communities/", include(("communities.api_urls",
                                      "communities_api"),
                                     namespace="communities_api")),

    # Swagger
    path("swagger/", schema_view.with_ui('swagger', cache_timeout=0),
         name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui('redoc', cache_timeout=0),
         name="schema-redoc"),
    path("swagger.json", schema_view.without_ui(cache_timeout=0),
         name="schema-json"),
    path("swagger.yaml", schema_view.without_ui(cache_timeout=0),
         name="schema-yaml"),

    # Spectacular
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
