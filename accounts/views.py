from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import ProfileForm
from .models import Profile


@login_required
def profile_view(request, username=None):
    if username:
        user_obj = get_object_or_404(User, username=username)
    else:
        user_obj = request.user

    profile = user_obj.profile

    num_posts = user_obj.post_set.count() \
        if hasattr(user_obj, "post_set") else 0
    num_comments = user_obj.comment_set.count() \
        if hasattr(user_obj, "comment_set") else 0

    return render(request, "accounts/profile.html", {
        "user_obj": user_obj,
        "profile": profile,
        "num_posts": num_posts,
        "num_comments": num_comments,
    })


@login_required
def settings_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)

        if request.POST.get('delete_avatar') == 'true':
            if profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None

        if request.POST.get('delete_banner') == 'true':
            if profile.banner:
                profile.banner.delete(save=False)
                profile.banner = None

        if form.is_valid():
            profile = form.save(commit=False)

            if 'nombre' in form.cleaned_data:
                request.user.first_name = form.cleaned_data['nombre']
                request.user.save()

            profile.save()
            form = ProfileForm(instance=profile)
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/settings.html', {
        'form': form,
        'profile': profile
    })
