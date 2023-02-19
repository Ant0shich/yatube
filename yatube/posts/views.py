from django.shortcuts import get_object_or_404, render, redirect
from .models import Post, Group, User
from django.core.paginator import Paginator
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import CommentForm, PostForm
from .models import Group, Post, Follow
from django.views.decorators.cache import cache_page


def paginator_obj(request, post_list):
    paginator = Paginator(post_list, settings.LIMIT_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page_obj = paginator_obj(request, post_list)
    names = 'Последние обновления на сайте'
    # Отдаем в словаре контекста
    context = {
        'page_obj': page_obj,
        'names': names,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = paginator_obj(request, post_list)
    context = {'group': group, 'page_obj': page_obj, }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = paginator_obj(request, post_list)
    return render(
        request,
        'posts/profile.html', {
            'page_obj': page_obj,
            'author': author,
        }
    )


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    return render(
        request,
        'posts/post_detail.html',
        {'post': post,
         'form': form,
         'comments': comments
         }
    )


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(
            'posts:profile',
            post.author.username
        )
    return render(
        request,
        'posts/create_post.html',
        {'form': form}
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(
        request, 'posts/includes/comments.html',
        {'form': form, 'user_post': post, 'author': post.author}
    )


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    post = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_obj(request, post)
    context = {'page_obj': page_obj, }
    return render(
        request, 'posts/follow.html', context
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if request.user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    get_object_or_404(
        Follow,
        user=request.user,
        author=author
    ).delete()
    return redirect('posts:profile', username=author)
