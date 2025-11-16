from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import ProfileForm
from .models import Profile
from blog.models import Post, Comment
from django.http import JsonResponse


@login_required
def profile_view(request, username=None):
    if username:
        user_obj = get_object_or_404(User, username=username)
    else:
        user_obj = request.user

    profile, created = Profile.objects.get_or_create(user=user_obj)

    posts = Post.objects.filter(author=user_obj)
    comments = Comment.objects.filter(author=user_obj)
    saved_posts = profile.saved_posts.all()

    return render(request, "accounts/profile.html", {
        "user_obj": user_obj,
        "profile": profile,
        "posts": posts,
        "comments": comments,
        "saved_posts": saved_posts,
        "num_posts": posts.count(),
        "num_comments": comments.count(),
    })


@login_required
def settings_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(instance=profile)

    if request.method == "POST":
        if 'generate_api_key' in request.POST:
            profile.generate_api_key()
        else:
            form = ProfileForm(request.POST, request.FILES, instance=profile)

            if request.POST.get('delete_avatar') == 'true' and profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None

            if request.POST.get('delete_banner') == 'true' and profile.banner:
                profile.banner.delete(save=False)
                profile.banner = None

            if form.is_valid():
                profile = form.save(commit=False)
                if 'nombre' in form.cleaned_data:
                    request.user.first_name = form.cleaned_data['nombre']
                    request.user.save()
                profile.save()
                form = ProfileForm(instance=profile)  # refrescamos el form

    return render(request, 'accounts/settings.html', {
        'form': form,
        'profile': profile
    })


@login_required
def toggle_saved_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    profile = request.user.profile

    if post in profile.saved_posts.all():
        profile.saved_posts.remove(post)
        saved = False
    else:
        profile.saved_posts.add(post)
        saved = True

    return JsonResponse({"saved": saved})


@login_required
def toggle_saved_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    profile = request.user.profile

    if comment in profile.saved_comments.all():
        profile.saved_comments.remove(comment)
        saved = False
    else:
        profile.saved_comments.add(comment)
        saved = True

    return JsonResponse({"saved": saved})
