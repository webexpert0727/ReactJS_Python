# -*- coding: utf-8 -*-
import factory

from ..models import BrewMethod, CoffeeGear


class CoffeeGearFactory(factory.django.DjangoModelFactory):
    name = 'NoName Gear'
    essentials = True
    model = '-'
    description = factory.Faker('text', max_nb_chars=100)
    more_info = factory.Faker('text', max_nb_chars=300)
    link = '#'
    price = 50
    in_stock = True
    available = True
    recommend = False
    special = ''
    allow_choice_package = False

    weight = 500

    @factory.post_generation
    def brew_methods(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for brew_method in extracted:
                self.brew_methods.add(brew_method)

    class Meta:
        model = CoffeeGear
        django_get_or_create = ('name',)


def create_initial_gears():
    if CoffeeGear.objects.all().count() > 0:
        return
    brews = BrewMethod.objects.all()
    CoffeeGearFactory(
        name='Marina Coffee Dripper', price=38, brew_methods=brews.filter(
            name_en='Drip'))
    CoffeeGearFactory(
        name='Donut Coffee Dripper', price=68, brew_methods=brews.filter(
            name_en='Drip'))
    CoffeeGearFactory(
        name='Aeropress Maker Kit', price=65, brew_methods=brews.filter(
            name_en='Aeropress'))
    CoffeeGearFactory(
        name='Kopi Sutra Drip Coffee Gift Set', price=20, special='set',
        brew_methods=brews.filter(name_en='Drip'))
    CoffeeGearFactory(
        name='Jamazing Drip Coffee Gift Set', price=20, in_stock=False,
        available=False, special='set', brew_methods=brews.filter(
            name_en='Drip'))
    CoffeeGearFactory(
        name='Breville Oracle', price=3598, weight=2000, essentials=False,
        brew_methods=brews.filter(name_en='None'))
