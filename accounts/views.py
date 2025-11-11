from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm
from .models import Profile


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")


@login_required
def settings_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            # Actualizamos request.user para usar el nombre visualizado
            request.user.first_name = profile.nombre
            request.user.save()
            form = ProfileForm(instance=profile)
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'accounts/settings.html',
                  {'form': form, 'profile': profile})
