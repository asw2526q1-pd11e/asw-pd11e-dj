from django.shortcuts import render, redirect
from .forms import PostForm
from .models.post import Post  # si tu modelo está en blog/models/post.py


def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()  # crea un Post en la base de datos
            return redirect('post_list')  # redirige a la lista de posts
    else:
        form = PostForm()  # formulario vacío para GET
    return render(request, 'blog/post_form.html', {'form': form})

def post_list(request):
    posts = Post.objects.all()
    return render(request, 'blog/post_list.html', {'posts': posts})