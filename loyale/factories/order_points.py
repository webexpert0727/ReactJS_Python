# -*- coding: utf-8 -*-
import factory

from ..models import OrderPoints


class OrderPointsFactory(factory.django.DjangoModelFactory):
    sub_regular = 200
    sub_special = 300
    sub_pod = 200
    one_regular = 50
    one_special = 75
    one_pod = 50
    credits = 1

    class Meta:
        model = OrderPoints


def create_initial_order_points():
    if OrderPoints.objects.all().count() > 0:
        return
    OrderPointsFactory()
