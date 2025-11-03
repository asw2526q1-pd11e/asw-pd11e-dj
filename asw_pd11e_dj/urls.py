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


# función para redirigir la raíz al listado de posts en el namespace 'blog'
def redirect_to_blog(request):
    return redirect("blog:post_list")
    

urlpatterns = [
    path("", redirect_to_blog),  # raíz → redirige a /blog/
    path("admin/", admin.site.urls),  # admin
    path("blog/", include(("blog.urls", "blog"), namespace="blog")),
    path("communities/", include(("communities.urls",
                                  "communities"), namespace="communities")),
]

# configuración de archivos estáticos y media en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
