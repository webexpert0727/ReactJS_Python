# -*- coding: utf-8 -*-
import factory

from django.utils import timezone

from ..models import BrewMethod, CoffeeType


CTZ = timezone.get_current_timezone()


class CoffeeTypeFactory(factory.django.DjangoModelFactory):
    name = 'NoName Coffee'
    mode = True
    special = False
    decaf = False
    maker = 'Pedro'
    region = 'Antioquia'
    country = 'CO'
    taste = 'Nutty and Tropical'
    more_taste = 'Imagine that delicate balance of juicy sweetness...'
    body = 3
    intensity = 6
    acidity = 'Medium'
    roasted_on = factory.Faker(
        'date_time_between', start_date='-2d', end_date='now', tzinfo=CTZ)
    shipping_till = factory.Faker(
        'date_time_between', start_date='+6d', end_date='+7d', tzinfo=CTZ)
    amount = 14
    amount_one_off = 18

    profile = {'1': 4, '2': 4, '3': 4, '4': 4, '5': 4, '6': 4}

    img = factory.django.ImageField()
    label = factory.django.FileField(filename='somelabel.png')
    label_drip = factory.django.FileField(filename='somelabel_drip.png')
    label_position = 1  # left
    description = 'This coffee is good'

    altitude = '2000m'
    varietal = 'Arabica'
    process = 'Fully Washed'

    weight = 200

    @factory.post_generation
    def brew_methods(self, create, extracted, **kwargs):
        # CoffeeTypeFactory.create(brew_methods=(brew_method1, brew_method2))
        if not create:
            return

        if extracted:
            for brew_method in extracted:
                self.brew_method.add(brew_method)
        else:
            self.brew_method.add(BrewMethod.objects.get(name_en='Espresso'))

    class Meta:
        model = CoffeeType
        django_get_or_create = ('name',)
        # exclude = ('label',)


def create_initial_coffees():
    if CoffeeType.objects.all().count() > 0:
        return
    brews = BrewMethod.objects.all()
    # 5 active bags coffee
    CoffeeTypeFactory(
        name='Ole Ola', brew_methods=brews.filter(name_en='None'))
    CoffeeTypeFactory(
        name='Piña Loca', brew_methods=brews.filter(
            name_en__in=['Drip', 'Aeropress', 'French press']))
    CoffeeTypeFactory(
        name='Guji Liya', brew_methods=brews.filter(
            name_en__in=['Aeropress', 'French press', 'None', 'Drip']))
    CoffeeTypeFactory(
        name='Shake Your Bun Bun!', brew_methods=brews.filter(
            name_en__in=['Aeropress', 'French press', 'Stove top', 'Espresso']))
    CoffeeTypeFactory(
        name='Give me S\'mores', brew_methods=brews.filter(
            name_en__in=['Stove top', 'Espresso']))
    # 1 special active bag coffee
    CoffeeTypeFactory(
        name='Eternal Sunshine', special=True,
        amount=18, amount_one_off=22, brew_methods=brews.filter(
            name_en__in=['Espresso', 'Drip', 'Aeropress', 'Cold Brew']))
    # 1 usual non active bag coffee
    CoffeeTypeFactory(
        name='Prosperoo', mode=False, brew_methods=brews.filter(
            name_en__in=['Drip', 'Aeropress']))
    # 2 active shotpods coffees
    CoffeeTypeFactory(
        name='Bird of Paradise Shotpods', brew_methods=brews.filter(
            name_en='Nespresso'))
    CoffeeTypeFactory(
        name='The Godfather ShotPods', brew_methods=brews.filter(
            name_en='Nespresso'))
    # 1 special active pod coffee
    CoffeeTypeFactory(
        name='Hakuna Matata Shotpods', special=True,
        amount=18, amount_one_off=22, brew_methods=brews.filter(
            name_en='Nespresso'))
    # 1 shotpods decaf active coffee
    CoffeeTypeFactory(
        name='Decaf Amigo', decaf=True, brew_methods=brews.filter(
            name_en='Nespresso'))
    # 1 shotpods non active coffee
    CoffeeTypeFactory(
        name='Jai Ho Shotpods', mode=False, brew_methods=brews.filter(
            name_en='Nespresso'))
    CoffeeTypeFactory(
        name='Discovery Pack', amount=18, amount_one_off=0,
        brew_methods=brews.filter(name_en__in=['Espresso', 'Cold Brew']))
