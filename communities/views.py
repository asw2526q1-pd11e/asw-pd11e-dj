from django.shortcuts import render, get_object_or_404, redirect
from .forms import CommunityForm
from .models import Community
from blog.models import Post
from django.contrib.auth.decorators import login_required
from django.db.models import Count


@login_required
def toggle_subscription(request, pk):
    community = get_object_or_404(Community, pk=pk)
    user = request.user

    if user in community.subscribers.all():
        community.subscribers.remove(user)  # unsubscribe
    else:
        community.subscribers.add(user)     # subscribe

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def community_create(request):
    if request.method == "POST":
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("communities:community_list")
    else:
        form = CommunityForm()
    return render(request, "communities/community_form.html", {"form": form})


def community_list(request):
    # Annotate each community with post and comment counts
    communities = Community.objects.annotate(
        real_posts=Count('posts', distinct=True),
        real_comments=Count('posts__comments', distinct=True)
    )

    community_data = []
    for c in communities:
        community_data.append({
            "obj": c,
            "subs": c.subscribers.count(),           # real subscriber count
            "posts": c.real_posts,                  # real posts
            "comments": c.real_comments,            # real comments
        })

    return render(
        request,
        "communities/community_list.html",
        {"community_data": community_data}
    )


def community_site(request, pk):
    # Annotate single community with post and comment counts
    community = get_object_or_404(
        Community.objects.annotate(
            real_posts=Count('posts', distinct=True),
            real_comments=Count('posts__comments', distinct=True)
        ),
        id=pk
    )

    posts = Post.objects.filter(
        communities=community
    ).order_by('-published_date')

    return render(
        request,
        'communities/community_site.html',
        {
            'community': community,
            'posts': posts,
            'subs': community.subscribers.count(),  # real subscriber count
            'posts_count': community.real_posts,    # real posts
            'comments_count': community.real_comments,  # real comments
        }
    )
