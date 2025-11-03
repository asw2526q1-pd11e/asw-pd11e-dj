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
    from .models import Community

    communities = Community.objects.all()
    return render(
        request, "communities/community_list.html",
        {"communities": communities}
    )


def community_site(request, pk):
    community = get_object_or_404(Community, id=pk)
    return render(request,
                  'communities/community_site.html',
                  {'community': community})