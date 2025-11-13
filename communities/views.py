from django.shortcuts import render, get_object_or_404, redirect
from .forms import CommunityForm
from .models import Community
from blog.models import Post
from django.contrib.auth.decorators import login_required
from django.db.models import Count


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
    communities = Community.objects.annotate(
        real_posts=Count('posts', distinct=True),
        real_comments=Count('posts__comments', distinct=True)
    )

    community_data = []
    for c in communities:
        community_data.append({
            "obj": c,
            "fake_subs": (c.id * 13) % 500 + 20,
            "fake_posts": c.real_posts,  # type: ignore
            "fake_comments": c.real_comments,  # type: ignore
        })

    return render(
        request,
        "communities/community_list.html",
        {"community_data": community_data}
    )


def community_site(request, pk):
    community = get_object_or_404(Community, id=pk)

    posts = (
        Post.objects
        .filter(communities=community)
        .order_by('-published_date')
    )

    fake_subs = (community.id * 13) % 500 + 20
    fake_comments = (community.id * 7) % 120 + 3

    return render(request,
                  'communities/community_site.html',
                  {
                      'community': community,
                      'posts': posts,
                      'fake_subs': fake_subs,
                      'fake_comments': fake_comments,
                  })
