# -*- coding: utf-8 -*-
import factory

from django.utils.text import slugify

from ..models import BrewMethod


class BrewMethodFactory(factory.django.DjangoModelFactory):
    name = 'Espresso'
    slug = factory.LazyAttribute(lambda obj: slugify(obj.name))
    img = factory.django.ImageField()

    class Meta:
        model = BrewMethod
        django_get_or_create = ('name',)


def create_initial_brew_methods():
    if BrewMethod.objects.all().count() > 0:
        return
    brew_methods = (
        'Espresso', 'Drip', 'Aeropress', 'French press', 'Stove top',
        'Cold Brew', 'None', 'Nespresso')
    for brew in brew_methods:
        BrewMethodFactory(name=brew)
