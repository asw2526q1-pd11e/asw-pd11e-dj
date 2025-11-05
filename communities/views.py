from django.shortcuts import render, get_object_or_404, redirect
from .forms import CommunityForm
from .models import Community
from blog.models import Post


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
    communities = Community.objects.all()

    community_data = []
    for c in communities:
        real_posts = c.posts.count()  # ✅ gràcies al related_name
        community_data.append({
            "obj": c,
            "fake_subs": (c.id * 13) % 500 + 20,
            "fake_comments": (c.id * 7) % 120 + 3,
            "fake_posts": real_posts,  # ✅ ara és real
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
