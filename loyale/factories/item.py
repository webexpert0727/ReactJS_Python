# -*- coding: utf-8 -*-
import factory

from ..models import Item


class ItemFactory(factory.django.DjangoModelFactory):
    name = 'NoName Item'
    description = factory.Faker('text', max_nb_chars=100)
    points = 0
    img = factory.django.ImageField()
    in_stock = True

    class Meta:
        model = Item
        django_get_or_create = ('name',)


def create_initial_loyale_items():
    if Item.objects.all().count() > 0:
        return
    ItemFactory(name='Free bag of coffee', points=1100)
    ItemFactory(name='Hario Hand Grinder', points=4000)
    ItemFactory(name='Hario Cold Brew Bottle', points=3500, in_stock=False)
    ItemFactory(name='Special surprise for invites', points=0)
