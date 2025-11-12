from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from blog.models import Post, Comment
from blog.forms import PostForm
from django.contrib.auth.decorators import login_required


def post_list(request):
    posts = Post.objects.all()
    return render(request, "blog/post_list.html", {"posts": posts})


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # ✅ usuario autenticado
            post.save()
            return redirect("blog:post_list")
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, "blog/post_detail.html", {"post": post})


@require_POST
@login_required
def upvote_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.votes += 1
    post.save()
    return redirect(request.META.get("HTTP_REFERER", "blog:post_list"))


@require_POST
@login_required
def downvote_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.votes -= 1
    post.save()
    return redirect(request.META.get("HTTP_REFERER", "blog:post_list"))


def get_comments_tree(post_id):
    def build_tree(comment):
        return {
            "id": comment.id,
            "author": comment.author.username,  # 👈 mostrar nombre del usuario
            "content": comment.content,
            "published_date": comment.published_date,
            "votes": comment.votes,
            "image": comment.image.url if comment.image else None,
            "replies": [build_tree(reply) for reply in comment.replies.all()],
        }

    root_comments = Comment.objects.filter(post_id=post_id, parent__isnull=True)
    return [build_tree(c) for c in root_comments]


def comments_index(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments_data = get_comments_tree(post.id)
    return JsonResponse(comments_data, safe=False)


@require_POST
@login_required
def comment_create(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = request.user  # ✅ usuario logueado
    content = request.POST.get("content")
    parent_id = request.POST.get("parent_id")
    image = request.FILES.get("image")

    parent_comment = None
    if parent_id:
        parent_comment = get_object_or_404(Comment, pk=parent_id, post=post)

    Comment.objects.create(
        post=post,
        author=author,
        content=content,
        published_date=timezone.now(),
        votes=0,
        parent=parent_comment,
        image=image,
    )

    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    else:
        return redirect("blog:post_detail", pk=post.id)


@require_POST
@login_required
def comment_upvote(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.votes += 1
    comment.save()
    return JsonResponse({"votes": comment.votes})


@require_POST
@login_required
def comment_downvote(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.votes -= 1
    comment.save()
    return JsonResponse({"votes": comment.votes})
