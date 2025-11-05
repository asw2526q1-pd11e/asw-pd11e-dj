from django.shortcuts import render, get_object_or_404, redirect
from .forms import CommunityForm
from .models import Community


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
        community_data.append({
            "obj": c,
            "fake_subs": (c.id * 13) % 500 + 20,
            "fake_comments": (c.id * 7) % 120 + 3,
            "fake_posts": (c.id * 5) % 80 + 1,
        })

    return render(
        request,
        "communities/community_list.html",
        {"community_data": community_data}
    )


def community_site(request, pk):
    community = get_object_or_404(Community, id=pk)
    return render(request,
                  'communities/community_site.html',
                  {'community': community})