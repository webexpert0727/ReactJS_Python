# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import render

from content.models import BrewGuide, Career
from coffees.models import CoffeeGear, BrewMethod

from django.contrib.sites.models import Site


def careers(request):
    careers = Career.objects.filter(active=True)

    context = {
        'current_domain': Site.objects.get_current().domain,
        'careers': careers
    }

    return render(request, 'content/careers.html', context)


def privacy(request):
    context = {
        'current_domain': Site.objects.get_current().domain
    }

    return render(request, 'content/privacy.html', context)


def blog(request):
    return None


class BrewGuideListView(ListView):
    model = BrewGuide
    context_object_name = 'brew_guides'
    template_name = 'content/brew_guides.html'


class BrewGuideDetailView(DetailView):
    model = BrewGuide
    context_object_name = 'brew_guide'
    template_name = 'content/brew_guide_details.html'

    def get_context_data(self, **kwargs):
        slug = self.kwargs.get('slug', None)
        context = super(BrewGuideDetailView, self).get_context_data(**kwargs)
        context['gears'] = CoffeeGear.objects.filter(brew_methods__slug__contains=slug)
        return context

