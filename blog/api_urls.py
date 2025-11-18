from django.urls import path
from .api_views import post_comments, post_comments_root, post_comments_tree, post_detail, post_list, search_posts_comments # noqa E501

app_name = "blog_api"

urlpatterns = [
    path('posts/', post_list, name='post_list'),
    path('posts/<int:pk>/', post_detail, name='post_detail'),
    path('posts/<int:pk>/comments/', post_comments, name='post_comments'),
    path('posts/<int:pk>/comments_tree/',
         post_comments_tree,
         name='post_comments_tree'),  # arbre complet
    path('posts/<int:pk>/comments_root/',
         post_comments_root,
         name='post_comments_root'),  # només 1r nivell
    path('search/', search_posts_comments, name='search_posts_comments'),
]
