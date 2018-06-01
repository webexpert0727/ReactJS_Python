# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations, models
from django.utils.timezone import now


def set_created_at(apps, schema_editor):
    MyUser = apps.get_model('customauth', 'MyUser')
    Order = apps.get_model('customers', 'Order')
    GearOrder = apps.get_model('customers', 'GearOrder')
    fake_datetime = MyUser.objects.earliest('id').account_creation_date
    for user in MyUser.objects.all():
        try:
            customer = user.customer
        except ObjectDoesNotExist as e:
            print 'Error: %r: [%d] %s' % (e, user.id, user.email)
            user.created_at = user.account_creation_date  # just to avoid error "created_at" contains null values
            user.save(update_fields=['created_at'])
            continue
        if user.account_creation_date > fake_datetime:
            user.created_at = user.account_creation_date  # real date
        else:
            orders = Order.objects.filter(customer=customer)
            gear_orders = GearOrder.objects.filter(customer=customer)
            first_coffee_order_date = (orders.only('date').earliest('date').date
                                       if orders.count() > 0 else now())
            first_gear_order_date = (gear_orders.only('date').earliest('date').date
                                     if gear_orders.count() > 0 else now())
            user.created_at = min([
                first_coffee_order_date, first_gear_order_date,
                user.account_creation_date])
        user.save(update_fields=['created_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('customauth', '0005_myuser_created_at'),
    ]

    operations = [
        migrations.RunPython(set_created_at),
        migrations.AlterField(
            model_name='myuser',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
