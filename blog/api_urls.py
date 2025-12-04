from django.urls import path
from .api_views import (post_comments, post_comments_root, post_comments_tree,
                        post_detail, post_list, post_list_ordered,
                        search_posts_comments,
                        UpvotePostAPIView,
                        DownvotePostAPIView, UpvoteCommentAPIView,
                        DownvoteCommentAPIView,
                        PostCreateAPIView, PostEditAPIView, DeletePostAPIView)

app_name = "blog_api"

urlpatterns = [
    path('api/posts/', post_list, name='post_list'),
    path('api/posts/<int:pk>/', post_detail, name='post_detail'),
    path('api/posts/<int:pk>/comments/', post_comments, name='post_comments'),
    path('api/posts/<int:pk>/comments_tree/',
         post_comments_tree,
         name='post_comments_tree'),  # arbre complet
    path('api/posts/<int:pk>/comments_root/',
         post_comments_root,
         name='post_comments_root'),
    path('api/search/', search_posts_comments, name='search_posts_comments'),
    path('posts/', post_list_ordered, name='post_list_ordered'),

    # POSTS
    path('api/posts/<int:pk>/upvote/',
         UpvotePostAPIView.as_view(),
         name='api_upvote_post'),
    path('api/posts/<int:pk>/downvote/',
         DownvotePostAPIView.as_view(),
         name='api_downvote_post'),
    path('api/posts/create/',
         PostCreateAPIView.as_view(), name='post-create'),
    path('api/posts/<int:pk>/edit/',
         PostEditAPIView.as_view(), name="post-edit"),
    path('api/posts/<int:pk>/delete/',
         DeletePostAPIView.as_view(), name="post-delete"),

    # COMMENTS
    path('api/comments/<int:comment_id>/upvote/',
         UpvoteCommentAPIView.as_view(),
         name='api_upvote_comment'),
    path('api/comments/<int:comment_id>/downvote/',
         DownvoteCommentAPIView.as_view(),
         name='api_downvote_comment'
         ),

]
