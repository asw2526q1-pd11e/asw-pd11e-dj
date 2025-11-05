from blog.models.post import Post
from blog.forms import PostForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST


def post_list(request):
    posts = Post.objects.all()
    return render(request, "blog/post_list.html", {"posts": posts})


def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("blog:post_list")
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "blog/post_detail.html", {"post": post})


@require_POST
def upvote_post(request, pk):
    try:
        post = Post.objects.get(pk=pk)
        post.votes += 1
        post.save()
    except Post.DoesNotExist:
        pass
    return redirect(request.META.get("HTTP_REFERER", "blog:post_list"))


@require_POST
def downvote_post(request, pk):
    try:
        post = Post.objects.get(pk=pk)
        post.votes -= 1
        post.save()
    except Post.DoesNotExist:
        pass
    return redirect(request.META.get("HTTP_REFERER", "blog:post_list"))
