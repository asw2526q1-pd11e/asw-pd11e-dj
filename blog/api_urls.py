from django.urls import path
from .api_views import post_comments, post_comments_root, post_comments_tree, post_detail, post_list, search_posts_comments, UpvotePostAPIView, DownvotePostAPIView, UpvoteCommentAPIView, DownvoteCommentAPIView  # noqa E501

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

    # POSTS
    path('api/posts/<int:pk>/upvote/',
         UpvotePostAPIView.as_view(),
         name='api_upvote_post'),
    path('api/posts/<int:pk>/downvote/',
         DownvotePostAPIView.as_view(),
         name='api_downvote_post'),

    # COMMENTS
    path('api/comments/<int:comment_id>/upvote/',
         UpvoteCommentAPIView.as_view(),
         name='api_upvote_comment'),
    path('api/comments/<int:comment_id>/downvote/',
         DownvoteCommentAPIView.as_view(),
         name='api_downvote_comment'
         ),
]
