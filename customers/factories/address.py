import factory

from django.db.models.signals import post_save

from . import CustomerFactory
from customers.models.address import Address

@factory.django.mute_signals(post_save)
class AddressFactory(factory.django.DjangoModelFactory):
    customer = factory.SubFactory(CustomerFactory)

    name = factory.Faker('state')
    recipient_name = factory.Faker('name')
    # TODO: if postcode checking will be add, use postcode from it
    line1 = factory.Faker('street_address')
    line2 = factory.Faker('secondary_address')
    postcode = factory.Faker('postcode')
    is_primary = factory.Faker('fake.boolean', chance_of_getting_true=50)

    class Params:
        pass

    class Meta:
        model = Address