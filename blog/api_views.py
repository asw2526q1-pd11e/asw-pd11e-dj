from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Post
from .serializers import PostSerializer


@api_view(['GET'])
def post_list(request):
    posts = Post.objects.all().order_by('-published_date')
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)
