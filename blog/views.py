from django.shortcuts import redirect, render
from django.utils.timezone import now
from el_pagination.views import AjaxListView

from blog.models import Category, Post


def index(request):
    context = {}
    context['latest_posts'] = Post.objects.all()\
        .filter(date_published__lte=now())\
        .order_by('-date_published')[:3]
    context['categories'] = [x for x in Category.objects.all() if Post.objects.filter(category=x)]

    context['latest_posts_in_category'] = {}
    for post in Post.objects.all().order_by('-date_published'):
        if post.category in context['latest_posts_in_category']:
            if len(context['latest_posts_in_category'][post.category]) < 4:
                context['latest_posts_in_category'][post.category].append(post)
        else:
            context['latest_posts_in_category'][post.category] = [post]

    context['pagename'] = 'blog'

    return render(request, 'blog/index.html', context)


def filter_posts(request, cat_slug=None, tag_slug=None, template='blog/categories.html'):
    print 'category', cat_slug
    print 'tag', tag_slug

    context = {}
    context['categories'] = [x for x in Category.objects.all() if Post.objects.filter(category=x)]
    if cat_slug and cat_slug != 'latest':
        try:
            context['category'] = Category.objects.get(slug=cat_slug)
            context['posts'] = Post.objects.filter(category=context['category'])\
                .filter(date_published__lte=now())\
                .order_by('-date_published')
        except Category.DoesNotExist:
            return redirect('blog')
        except Post.DoesNotExist:
            return redirect('blog')

    elif tag_slug:
        context['posts'] = Post.objects.filter(tags__slug__contains=tag_slug)
        if len(context['posts']) == 0:
            return redirect('filter-posts-by-cat')
    else:
        # latest posts
        context['category'] = 'Latest'
        context['posts'] = Post.objects.all()\
            .filter(date_published__lte=now())\
            .order_by('-date_published')

    context['page_template'] = 'blog/categories-page.html'

    if request.is_ajax():
        template = context['page_template']

    context['pagename'] = 'blog'

    return render(request, template, context)


def get_post(request, slug):
    context = {}
    print 'post', slug

    try:
        context['post'] = Post.objects.get(slug=slug)
    except Post.DoesNotExist:
        return redirect('filter-posts-by-cat')

    context['pagename'] = 'blog'
    context['categories'] = [x for x in Category.objects.all() if Post.objects.filter(category=x)]

    return render(request, 'blog/post.html', context)
