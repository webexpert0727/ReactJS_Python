from django.utils import timezone

from decimal import Decimal
from django.db import models
from django_extensions.db.fields.json import JSONField
from django_hstore import hstore
from picklefield import PickledObjectField

from coffees.models import RawBean
from customers.models import Customer
from customers.models import Order, GearOrder


class MailchimpCampaignStats(models.Model):
    NO_ACTION = 'NA'
    GET_STARTED = 'GS'
    PURCHASED = 'PU'

    ACTION_CHOICES = (
        (NO_ACTION, 'No Action'),
        (GET_STARTED, 'Visited Get Started'),
        (PURCHASED, 'Purchased')
    )

    action = models.CharField(
        verbose_name="Action",
        max_length=16,
        choices=ACTION_CHOICES,
        default=NO_ACTION
    )

    order = models.ForeignKey(Order, null=True, blank=True, default = None)
    email = models.CharField("email",
                             max_length=255)

    campaign_id = models.CharField("First name",max_length=255)


    @classmethod
    def create(cls, campaign_id, action, email, order):
        mc_c_o = cls(campaign_id=campaign_id, action=action, email=email, order=order)
        return mc_c_o

    # def __unicode__(self):
    #     return 'Created on: {:20}| from Campaign {}| using KOPIKAKI'.format(
    #         timezone.localtime(self.date).strftime('%b, %d (%H:%M)'),
    #         self.campaign_id
    #     )



# FYP data collection related models
class FYPOrderStats(models.Model):
    order = models.ForeignKey(Order)
    date = models.DateTimeField(
        verbose_name='Order time',
        auto_now_add=True
    )

    @classmethod
    def create(cls, order):
        orderstats = cls(order=order)
        # do something with the book
        return orderstats

    # def __unicode__(self):
    #     return 'Order id {}| processed on: {:20}| using KOPIKAKI'.format(
    #         self.order.id,
    #         timezone.localtime(self.date).strftime('%b, %d (%H:%M)'),
        # )


class ChurnRateData(models.Model):
    month_year = models.CharField("Month and Year",
                             max_length=255)
    proportion_churned = models.DecimalField(
        verbose_name='Proportion Churned',
        max_digits=10,
        decimal_places=6,
        default=0)


class RawBeanStats(models.Model):
    raw_bean = models.ForeignKey(RawBean)
    date = models.DateTimeField(
        verbose_name='Transaction Date',
        auto_now_add=True
    )
    stock = models.DecimalField('Stock', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    status = models.BooleanField('Available', default=True)

    def __unicode__(self):
        return '%s: %skg: %s: %s' % (self.raw_bean.name, self.stock, self.date, self.status)


class IntercomLocal(models.Model):
    customer = models.ForeignKey(Customer)
    event = models.CharField("event_name",
                             max_length=255)
    data = JSONField()
    added_timestamp = models.DateTimeField('added', auto_now_add=True)

    def __unicode__(self):
        return 'Customer %s did %s at %s' % (self.customer.get_full_name(), self.event, self.added_timestamp)


class Threshold(models.Model):
    amount = models.DecimalField('Threshold amount', max_digits=6, decimal_places=2, default=Decimal('20.00'))
    date = models.DateTimeField(
        verbose_name='Latest Update',
        auto_now_add=True
    )

    def __unicode__(self):
        return 'Threshold: %s, Latest Update: %s' % (self.amount, self.date)


class ReportCard(models.Model):
    date = models.DateTimeField(verbose_name='Date Generated')

    active_customers = models.IntegerField('Number of Active Customers', null=False, blank=False)
    orders = models.IntegerField('Number of orders', null=False, blank=False)
    churn = models.IntegerField('Number of people who churn', null=False, blank=False)
    new_signups = models.IntegerField('Number of new signups', null=False, blank=False)
    expected_demand = models.FloatField('Expected Demand', default=float(Decimal('0.00')))
    demand_actualising = models.FloatField('Probability of demand actualising', default=float(Decimal('0.00')))
    deviation = models.FloatField('Deviation from recommendation', default=float(Decimal('0.00')))

    actions = hstore.SerializedDictionaryField(default={})

    percentage_changes = hstore.SerializedDictionaryField(default={})

    objects = hstore.HStoreManager()


class Recommendation(models.Model):
    date = models.DateTimeField(
        verbose_name='Date Generated',
        auto_now_add=True
    )

    facebook_advertising_cost = models.DecimalField('Amount spent on Facebook Advertising', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    adwords_cost = models.DecimalField('Amount spent on Google Adwords', max_digits=10, decimal_places=2, default=Decimal('0.00'))
    new_coffees = models.IntegerField('Number of new coffees introduced', default=0)
    email_campaigns = models.IntegerField('Number of email campaigns sent', default=0)
    roadshows = models.IntegerField('Number of roadshows conducted', default=0)
    blog_posts = models.IntegerField('Number of blogposts posted', default=0)
    budget = models.IntegerField('Abstract budget for calculation', default=0)

    expected_demand = models.FloatField('Expected Demand', default=float(Decimal('0.00')))
    demand_actualising = models.FloatField('Probability of demand actualising', default=float(Decimal('0.00')))


class ClusterDF(models.Model):
    data = PickledObjectField()


class CustomerCluster(models.Model):
    cluster_number = models.IntegerField('Cluster Number', null=False, blank=False, unique=True)
    cluster_name = models.CharField("Cluster Name", max_length=255, null=False, blank=False)
    cluster_description = models.CharField("Cluster Description", max_length=255, null=False, blank=False)
    mean_orders = models.DecimalField('Mean Number of Orders', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    mean_ratio_amount_time = models.DecimalField('Mean Ratio of Amount Spent against Time', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    mean_vouchers_used = models.DecimalField('Mean Number of Vouchers Used', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    mean_interval = models.DecimalField('Mean Interval between orders(in days)', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    mean_total_spending = models.DecimalField('Mean Total Spending', max_digits=6, decimal_places=2, default=Decimal('0.00'))
    mean_one_off_orders = models.DecimalField('Mean Number of One-Off orders', max_digits=6, decimal_places=2,default=Decimal('0.00'))
    cluster_revenue = models.DecimalField('Total revenue earned from customers in cluster', max_digits=10, decimal_places=2,default=Decimal('0.00'))

    customers = hstore.SerializedDictionaryField(default={})
    percentage_brew_methods = hstore.SerializedDictionaryField(default={})

    def __unicode__(self):
        return 'Cluster Number: %s, Cluster Description: %s, Mean Number of Orders: %s, Mean Ratio of Amount Spent against Time: %s, ' \
               'Mean Number of Vouchers Used: %s, Mean Interval between oredrs(in days): %s' % (self.cluster_number, self.cluster_description, self.mean_orders,
                                                                                                self.mean_ratio_amount_time, self.mean_vouchers_used, self.mean_interval)

class RightsSupport(models.Model):
    class Meta:
        managed = False  # No database table creation or deletion operations \
        # will be performed for this model.

        permissions = (
            ('can_view_pack', 'Can View the Packing Page'),
            ('can_view_customers', 'Can View the Customer Page'),
            ('can_view_inventory', 'Can View the Inventory Page'),
            ('can_view_marketing', 'Can View the Marketing Page'),
            ('can_view_analysis', 'Can View the Analysis Page'),
        )

class RoadbullOrder(models.Model):
    gear_order = models.ForeignKey(GearOrder, related_name='roadbull')
    order_number = models.CharField(max_length=32)
    consignment_number = models.CharField(max_length=32)
    tracking_number = models.CharField(max_length=32)
    bar_code_url = models.CharField(max_length=128)
    qr_code_url = models.CharField(max_length=128)
    label_pdf = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.gear_order)
