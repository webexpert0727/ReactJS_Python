
import factory

from django.db.models.signals import post_save
from django.utils import timezone

from coffees.models import BrewMethod, CoffeeType

from . import CustomerFactory
from ..models import Order, Preferences


CTZ = timezone.get_current_timezone()


@factory.django.mute_signals(post_save)
class OrderFactory(factory.django.DjangoModelFactory):
    customer = factory.SubFactory(CustomerFactory)
    date = factory.Faker(
        'date_time_between', start_date='-9d', end_date='-4d', tzinfo=CTZ)
    shipping_date = factory.Faker(
        'date_time_between', start_date='-2d', end_date='-1d', tzinfo=CTZ)
    status = Order.ACTIVE
    voucher = None
    address = None
    coffee = factory.Iterator(
        CoffeeType.objects.bags().filter(special=False))
    different = False
    interval = 7
    amount = factory.LazyAttribute(
        lambda obj: (obj.coffee.amount if obj.recurrent else
                     obj.coffee.amount_one_off)
    )
    recurrent = False
    brew = factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso'))
    package = Preferences.GRINDED
    details = {}
    resent = False
    custom_price = False

    class Params:
        bag_sub_special = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.bags()
                .filter(special=True)),
            recurrent=True,
            brew=factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso')),
        )
        bag_one_special = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.bags()
                .filter(special=True)),
            recurrent=False,
            brew=factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso')),
        )
        bag_sub = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.bags()
                .filter(special=False)),
            recurrent=True,
            brew=factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso')),
        )
        bag_one = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.bags()
                .filter(special=False)),
            recurrent=False,
            brew=factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso')),
        )
        pod_sub_special = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.nespresso()
                .filter(special=True)),
            recurrent=True,
            brew=factory.Iterator(BrewMethod.objects.filter(name_en='Nespresso')),
        )
        pod_one_special = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.nespresso()
                .filter(special=True)),
            recurrent=False,
            brew=factory.Iterator(BrewMethod.objects.filter(name_en='Nespresso')),
        )
        pod_sub = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.nespresso()
                .filter(special=False)),
            recurrent=True,
            brew=factory.Iterator(BrewMethod.objects.filter(name_en='Nespresso')),
        )
        pod_one = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.nespresso()
                .filter(special=False)),
            recurrent=False,
            brew=factory.Iterator(BrewMethod.objects.filter(name_en='Nespresso')),
        )
        pod_sub_decaf = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.nespresso()
                .filter(special=False, decaf=True)),
            recurrent=True,
            brew=factory.Iterator(BrewMethod.objects.filter(name_en='Nespresso')),
        )
        discovery_pack = factory.Trait(
            coffee=factory.Iterator(
                CoffeeType.objects.tasters()
                .filter(special=False)),
            recurrent=True,
            brew=factory.Iterator(BrewMethod.objects.exclude(name_en='Nespresso')),
        )

    class Meta:
        model = Order
