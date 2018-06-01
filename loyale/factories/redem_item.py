# -*- coding: utf-8 -*-
import factory

from customauth.factories import UserFactory

from customers.factories import CustomerFactory

from giveback_project.helpers import get_shipping_date

from ..models import Item, RedemItem


class RedemItemFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    status = 'pending'
    item = factory.Iterator(Item.objects.all())
    points = factory.SelfAttribute('item.points')  # factory.LazyAttribute(lambda obj: obj.item.points)
    shipping_date = factory.LazyFunction(get_shipping_date)

    class Meta:
        model = RedemItem

    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        super(RedemItemFactory, cls)._after_postgeneration(obj, create, results)
        if create:
            CustomerFactory(user=obj.user)
