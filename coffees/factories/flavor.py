# -*- coding: utf-8 -*-
import factory

from ..models import Flavor


class FlavorFactory(factory.django.DjangoModelFactory):
    name = 'None'
    img = factory.django.ImageField()

    class Meta:
        model = Flavor
        django_get_or_create = ('name',)


def create_initial_flavors():
    if Flavor.objects.all().count() > 0:
        return
    flavors = (
        'Berries', 'Caramel', 'Chocolate', 'Citrus Lemons', 'Edible Flowers',
        'Stone Fruits', 'None')
    for flavor in flavors:
        FlavorFactory(name=flavor)
