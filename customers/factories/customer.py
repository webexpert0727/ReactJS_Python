import factory

from django.db.models.signals import post_save

from customauth.factories import UserFactory

from .preferences import PreferencesFactory
from ..models import Customer


@factory.django.mute_signals(post_save)
class CustomerFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    country = 'SG'
    line1 = factory.Faker('street_address')
    line2 = factory.Faker('city')
    postcode = factory.Faker('postalcode')
    stripe_id = factory.Sequence(lambda n: 'cus_%014d' % n)
    amount = 0
    extra = {}
    # vouchers = models.ManyToManyField(Voucher)
    # received_coffee_samples = models.ManyToManyField(CoffeeType)

    preferences = factory.RelatedFactory(PreferencesFactory, 'customer')

    class Meta:
        model = Customer

    class Params:
        worldwide = factory.Trait(
            country=factory.Iterator(['FR', 'DE', 'US', 'GB', 'RU'])
        )

    @factory.lazy_attribute
    def phone(self):
        return factory.Faker('phone_number').generate({})[:10]

    @factory.lazy_attribute
    def card_details(self):
        return '%(last4)s%(expire)s' % {
            'last4': factory.Faker('credit_card_number').generate({})[-4:],
            'expire': (factory.Faker('credit_card_expire', date_format='%m%Y')
                              .generate({}))}
