from django.shortcuts import render, redirect
from .forms import CommunityForm

def community_create(request):
    if request.method == "POST":
        form = CommunityForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('community_list')
    else:
        form = CommunityForm()
    return render(request, 'communities/community_form.html', {'form': form})

def community_list(request):
    from .models import Community
    communities = Community.objects.all()
    return render(request, 'communities/community_list.html', {'communities': communities})
