from rest_framework import serializers
from .models import Post, Comment
from communities.models import Community

# -------------------- SERIALIZERS --------------------


class PostSerializer(serializers.ModelSerializer):
    title = serializers.CharField(help_text="Títol del post, "
                                            "màxim 200 caràcters")
    content = serializers.CharField(help_text="Contingut "
                                              "complet del post")
    author = serializers.CharField(source="author.username",
                                   help_text="Nom d'usuari de l'autor")
    published_date = serializers.DateTimeField(help_text="Data de publicació")
    votes = serializers.IntegerField(help_text="Número de vots del post")
    url = serializers.CharField(help_text="URL absoluta del post")
    image = serializers.ImageField(
        allow_null=True,
        help_text="URL de la imatge del post, si existeix"
    )
    communities = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name',
        help_text="Llista de noms de comunitats a les quals pertany el post"
    )

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author',
                  'published_date', 'votes', 'url',
                  'image', 'communities']
        ref_name = "PostSerializerWithCommunities"


class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating posts via the API.
    Accepts communities by their name (string) instead of ID.
    """
    communities = serializers.SlugRelatedField(
        queryset=Community.objects.all(),
        many=True,
        required=True,
        slug_field='name',
        help_text="Llista de noms de comunitats (accepta més d'una comunitat)"
    )

    title = serializers.CharField(
        max_length=200,
        help_text="Títol del post (màxim 200 caràcters)"
    )

    content = serializers.CharField(
        help_text="Contingut complet del post",
        style={'base_template': 'textarea.html'}
    )

    url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text="Enllaç d'interès (opcional)"
    )

    image = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Imatge del post (opcional)"
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'image', 'url', 'communities']

    def create(self, validated_data):
        communities_data = validated_data.pop('communities', [])
        post = Post.objects.create(**validated_data)
        post.communities.set(communities_data)
        return post


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=True)
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)


class CommentEditSerializer(serializers.ModelSerializer):
    content = serializers.CharField(required=False,
                                    allow_blank=True, default="")
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ["content", "image"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not rep.get("content"):
            rep["content"] = ""
        if not rep.get("image"):
            rep["image"] = None
        return rep


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username",
                                   help_text="Nom d'usuari de "
                                             "l'autor del comentari")
    image = serializers.ImageField(help_text="URL de la imatge del comentari, "
                                             "si existeix", allow_null=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'content', 'author',
                  'published_date', 'votes', 'url', 'image']


class CommentTreeSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username",
                                   help_text="Nom d'usuari de "
                                             "l'autor del comentari")
    image = serializers.ImageField(allow_null=True,
                                   help_text="URL de la imatge "
                                             "del comentari, si existeix")
    replies = serializers.SerializerMethodField(
        help_text="Llista de respostes (comentaris fills) "
                  "en estructura recursiva")

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author',
                  'published_date', 'votes',
                  'image', 'replies']

    def get_replies(self, obj):
        children = obj.replies.all().order_by('published_date')
        serializer = CommentTreeSerializer(children, many=True)
        return serializer.data


class PostUpdateSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=False, allow_blank=True, default="")
    content = serializers.CharField(required=False,
                                    allow_blank=True, default="")
    url = serializers.URLField(required=False, allow_blank=True, default="")
    image = serializers.ImageField(required=False, allow_null=True)
    communities = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        required=False,
        default=[""],
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'url', 'image', 'communities']

    def validate_communities(self, value):
        if not value:
            raise serializers.ValidationError("El post "
                                              "ha de tenir almenys "
                                              "una comunitat.")
        return value

    def update(self, instance, validated_data):
        communities_names = validated_data.pop('communities', None)
        if communities_names is not None:
            communities_qs = Community.objects.filter(
                name__in=communities_names)
            if not communities_qs.exists():
                raise serializers.ValidationError("Cap de "
                                                  "les comunitats "
                                                  "indicades existeix.")
            instance.communities.set(communities_qs)

        return super().update(instance, validated_data)


class SavedPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username',
                                        read_only=True)
    author_bio = serializers.CharField(source='author.profile.bio',
                                       default='Este usuario no '
                                               'ha comentado nada.',
                                       read_only=True)
    communities = serializers.StringRelatedField(many=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author_name', 'author_bio',
                  'published_date', 'votes', 'image_url', 'url', 'communities']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class PostDeleteSerializer(serializers.Serializer):
    detail = serializers.CharField(
        help_text="Missatge de confirmació de l'eliminació")
