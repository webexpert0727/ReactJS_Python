from django.shortcuts import render
from django.http import HttpResponse
# from content.models import News
from content.models import Section, Post
from giveback_project.helpers import geo_check
from django.contrib.sites.models import Site


@geo_check
def index(request, is_worldwide):
    context = {
        'is_worldwide': is_worldwide,
        'current_domain': Site.objects.get_current().domain,
    }
    return render(request, 'about/about.html', context)


@geo_check
def faq(request, is_worldwide):
    sections = Section.objects.all()
    posts = Post.objects.all()

    context = {
        'is_worldwide': is_worldwide,
        'sections': sections,
        'posts': posts,
        'current_domain': Site.objects.get_current().domain,
    }
    return render(request, 'about/faq.html', context)


def hookcoffee_academy(request):
    return render(request, 'about/hookcoffee_academy.html')
