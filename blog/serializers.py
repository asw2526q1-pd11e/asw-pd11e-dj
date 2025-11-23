from rest_framework import serializers
from .models import Post, Comment


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username',
                                        read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author_name', 'content',
                  'published_date', 'votes', 'url',
                  'image_url', 'is_root_comment', 'parent']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username',
                                        read_only=True)
    author_bio = serializers.CharField(source='author.profile.bio',
                                       default='Este usuario '
                                               'no ha comentado nada.',
                                       read_only=True)
    communities = serializers.StringRelatedField(many=True)
    image_url = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author_name',
                  'author_bio', 'published_date',
                  'votes', 'image_url', 'url', 'communities', 'comments']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
