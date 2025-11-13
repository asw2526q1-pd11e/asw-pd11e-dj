from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.utils import timezone
from blog.models import Post, Comment
from blog.models.votes import VotePost, VoteComment
from blog.forms import PostForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Only the author can edit
    if request.user != post.author:
        return HttpResponseForbidden("No tens permís per editar aquest post.")

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)

    return render(request, "blog/post_form.html", {"form": form, "post": post})


def post_list(request):
    posts = Post.objects.all()
    posts_data = []

    for post in posts:
        user_vote = 0
        if request.user.is_authenticated:
            vote_obj = VotePost.objects.filter(user=request.user,
                                               post=post).first()
            if vote_obj:
                user_vote = vote_obj.vote
        posts_data.append({"post": post, "user_vote": user_vote})

    return render(request, "blog/post_list.html", {"posts_data": posts_data})


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()
            return redirect("blog:post_list")
    else:
        form = PostForm()
    return render(request, "blog/post_form.html", {"form": form})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    user_vote = 0
    if request.user.is_authenticated:
        vote_obj = VotePost.objects.filter(user=request.user,
                                           post=post).first()
        if vote_obj:
            user_vote = vote_obj.vote  # 1, -1 o 0

    return render(request, "blog/post_detail.html",
                  {"post": post, "user_vote": user_vote})


# ------------------- POSTS VOTES ------------------- #
@require_POST
@login_required
def upvote_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    vote_obj, _ = VotePost.objects.get_or_create(user=request.user, post=post)

    if vote_obj.vote == 1:
        pass
    else:
        post.votes += 1
        vote_obj.vote += 1
        vote_obj.save()
        post.save()

    return redirect(request.META.get("HTTP_REFERER", "blog:post_list"))


@require_POST
@login_required
def downvote_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    vote_obj, _ = VotePost.objects.get_or_create(user=request.user, post=post)

    if vote_obj.vote == -1:
        pass
    else:
        post.votes -= 1
        vote_obj.vote -= 1
        vote_obj.save()
        post.save()

    return redirect(request.META.get("HTTP_REFERER", "blog:post_list"))


# ------------------- COMMENTS VOTES ------------------- #
@require_POST
@login_required
def comment_upvote(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    vote_obj, _ = VoteComment.objects.get_or_create(user=request.user,
                                                    comment=comment)

    if vote_obj.vote == 1:
        pass
    else:
        comment.votes += 1
        vote_obj.vote += 1
        vote_obj.save()
        comment.save()

    return JsonResponse({"votes": comment.votes})


@require_POST
@login_required
def comment_downvote(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    vote_obj, _ = VoteComment.objects.get_or_create(user=request.user,
                                                    comment=comment)

    if vote_obj.vote == -1:
        pass
    else:
        comment.votes -= 1
        vote_obj.vote -= 1
        vote_obj.save()
        comment.save()

    return JsonResponse({"votes": comment.votes})


# ------------------- COMMENTS TREE Y CREACIÓN ------------------- #

def get_comments_tree(post_id, user=None, order="top"):
    def build_tree(comment):
        user_vote = 0
        if user and user.is_authenticated:
            vote_obj = VoteComment.objects.filter(
                user=user,
                comment=comment).first()
            user_vote = vote_obj.vote if vote_obj else 0
        return {
            "id": comment.id,
            "author": comment.author.username,
            "content": comment.content,
            "published_date": comment.published_date,
            "votes": comment.votes,
            "image": comment.image.url if comment.image else None,
            "user_vote": user_vote,
            "replies": sorted(
                [build_tree(reply) for reply in comment.replies.all()],
                key=lambda x: (
                    -x["votes"] if order == "top"
                    else x["published_date"] if order == "old"
                    else -x["published_date"].timestamp()
                )
            ),
        }

    # Define order for root comments
    if order == "top":
        root_comments = Comment.objects.filter(
            post_id=post_id,
            parent__isnull=True).order_by(
                "-votes",
                "-published_date")
    elif order == "old":
        root_comments = Comment.objects.filter(
            post_id=post_id,
            parent__isnull=True).order_by(
                "published_date")
    else:  # "new"
        root_comments = Comment.objects.filter(
            post_id=post_id,
            parent__isnull=True).order_by(
                "-published_date")

    return [build_tree(c) for c in root_comments]


def comments_index(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    order = request.GET.get("order", "top")  # 'top', 'new', or 'old'
    comments_data = get_comments_tree(post.id, request.user, order)
    return JsonResponse(comments_data, safe=False)


@require_POST
@login_required
def comment_create(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = request.user
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


def search_view(request):
    query = request.GET.get("q", "")
    search_type = request.GET.get("type", "both")  # posts, comments, both
    results = []
    posts_results = []
    comments_results = []

    if query:
        if search_type == "posts":
            results = Post.objects.filter(title__icontains=query)
        elif search_type == "comments":
            results = Comment.objects.filter(content__icontains=query)
        elif search_type == "both":
            posts_results = Post.objects.filter(title__icontains=query)
            comments_results = Comment.objects.filter(content__icontains=query)

    context = {
        "results": results,
        "query": query,
        "search_type": search_type,
        "posts_results": posts_results,
        "comments_results": comments_results,
    }
    return render(request, "blog/search_results.html", context)


@login_required
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Solo el autor puede borrar su post
    if request.user != post.author:
        return HttpResponseForbidden("No pots esborrar aquest post.")

    # Django borrará automáticamente los comentarios en cascada
    post.delete()

    return redirect("blog:post_list")


@login_required
@require_POST
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    # Solo el autor puede borrar su comentario
    if request.user != comment.author:
        return HttpResponseForbidden("No pots esborrar aquest comentari.")

    # 🔁 Borrado recursivo de replies
    def delete_with_replies(c):
        for reply in c.replies.all():
            delete_with_replies(reply)
        c.delete()

    delete_with_replies(comment)

    # Respuesta JSON si viene de AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True})
    else:
        return redirect(request.META.get("HTTP_REFERER",
                                         f"/blog/posts/{comment.post.id}/"))


@login_required
@require_POST
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)

    # Solo el autor puede editar su comentario
    if request.user != comment.author:
        return HttpResponseForbidden("No pots editar aquest comentari.")

    new_content = request.POST.get("content", "").strip()
    if new_content:
        comment.content = new_content
        comment.save()
        return JsonResponse({"success": True, "new_content": new_content})
    else:
        return JsonResponse({"success": False, "error":
                             "El contingut no pot estar buit."})
