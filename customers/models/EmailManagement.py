from django.db import models

from customers.models import Customer, Order

from django_hstore import hstore


class EmailManagement(models.Model):
    token = models.CharField(max_length=64, primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.deletion.SET_NULL, related_name='%(class)ss', null=True, blank=True)
    action = hstore.DictionaryField(default={})
    active = models.BooleanField(default=True)
    order = models.ForeignKey(Order, on_delete=models.deletion.SET_NULL, related_name='%(class)ss', blank=True, null=True)

    objects = hstore.HStoreManager()

    def __unicode__(self):
        return '{} [{}]'.format(self.customer.user.email, self.order.id if self.order else '  -  ')
