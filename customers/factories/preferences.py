import factory

from coffees.models import BrewMethod, CoffeeType, Flavor

from ..models import Preferences


class PreferencesFactory(factory.django.DjangoModelFactory):
    customer = None
    coffee = factory.Iterator(CoffeeType.objects.bags())
    brew = factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso'))
    package = Preferences.WHOLEBEANS
    decaf = False
    different = False
    different_pods = False
    cups = 7
    intense = 5
    interval = 7
    interval_pods = 7
    force_coffee = False
    force_coffee_pods = False
    present_next = False

    class Meta:
        model = Preferences
        django_get_or_create = ('customer',)

    @factory.post_generation
    def flavors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for flavor in extracted:
                self.flavor.add(flavor)
        else:
            self.flavor.add(Flavor.objects.get(name_en='None'))
