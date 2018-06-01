
import factory

from django.db.models.signals import post_save
from django.utils import timezone

from coffees.models import CoffeeGear

from . import CustomerFactory
from ..models import GearOrder


CTZ = timezone.get_current_timezone()


@factory.django.mute_signals(post_save)
class GearOrderFactory(factory.django.DjangoModelFactory):
    customer = factory.SubFactory(CustomerFactory)
    date = factory.Faker(
        'date_time_between', start_date='-9d', end_date='-4d', tzinfo=CTZ)
    shipping_date = factory.Faker(
        'date_time_between', start_date='-2d', end_date='-1d', tzinfo=CTZ)
    status = GearOrder.ACTIVE
    voucher = None
    address = None
    gear = factory.Iterator(CoffeeGear.objects.all())
    price = factory.LazyAttribute(lambda obj: obj.gear.price)
    tracking_number = ''
    details = {}

    class Params:
        pass

    class Meta:
        model = GearOrder
