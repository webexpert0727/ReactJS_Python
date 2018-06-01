# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django_hstore.fields
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0003_auto_20161005_0138'),
    ]

    operations = [
        migrations.CreateModel(
            name='RightsSupport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'managed': False,
                'permissions': (('can_view_pack', 'Can View the Packing Page'), ('can_view_customers', 'Can View the Customer Page'), ('can_view_inventory', 'Can View the Inventory Page'), ('can_view_marketing', 'Can View the Marketing Page'), ('can_view_analysis', 'Can View the Analysis Page')),
            },
        ),
        migrations.CreateModel(
            name='ClusterDF',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', picklefield.fields.PickledObjectField(editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='CustomerCluster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cluster_number', models.IntegerField(unique=True, verbose_name=b'Cluster Number')),
                ('cluster_name', models.CharField(max_length=255, verbose_name=b'Cluster Name')),
                ('cluster_description', models.CharField(max_length=255, verbose_name=b'Cluster Description')),
                ('mean_orders', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Mean Number of Orders', max_digits=6, decimal_places=2)),
                ('mean_ratio_amount_time', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Mean Ratio of Amount Spent against Time', max_digits=6, decimal_places=2)),
                ('mean_vouchers_used', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Mean Number of Vouchers Used', max_digits=6, decimal_places=2)),
                ('mean_interval', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Mean Interval between orders(in days)', max_digits=6, decimal_places=2)),
                ('mean_total_spending', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Mean Total Spending', max_digits=6, decimal_places=2)),
                ('mean_one_off_orders', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Mean Number of One-Off orders', max_digits=6, decimal_places=2)),
                ('cluster_revenue', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Total revenue earned from customers in cluster', max_digits=10, decimal_places=2)),
                ('customers', django_hstore.fields.SerializedDictionaryField(default={})),
                ('percentage_brew_methods', django_hstore.fields.SerializedDictionaryField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Date Generated')),
                ('facebook_advertising_cost', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Amount spent on Facebook Advertising', max_digits=10, decimal_places=2)),
                ('adwords_cost', models.DecimalField(default=Decimal('0.00'), verbose_name=b'Amount spent on Google Adwords', max_digits=10, decimal_places=2)),
                ('new_coffees', models.IntegerField(default=0, verbose_name=b'Number of new coffees introduced')),
                ('email_campaigns', models.IntegerField(default=0, verbose_name=b'Number of email campaigns sent')),
                ('roadshows', models.IntegerField(default=0, verbose_name=b'Number of roadshows conducted')),
                ('blog_posts', models.IntegerField(default=0, verbose_name=b'Number of blogposts posted')),
                ('budget', models.IntegerField(default=0, verbose_name=b'Abstract budget for calculation')),
                ('expected_demand', models.FloatField(default=0.0, verbose_name=b'Expected Demand')),
                ('demand_actualising', models.FloatField(default=0.0, verbose_name=b'Probability of demand actualising')),
            ],
        ),
        migrations.CreateModel(
            name='ReportCard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(verbose_name=b'Date Generated')),
                ('active_customers', models.IntegerField(verbose_name=b'Number of Active Customers')),
                ('orders', models.IntegerField(verbose_name=b'Number of orders')),
                ('churn', models.IntegerField(verbose_name=b'Number of people who churn')),
                ('new_signups', models.IntegerField(verbose_name=b'Number of new signups')),
                ('expected_demand', models.FloatField(default=0.0, verbose_name=b'Expected Demand')),
                ('demand_actualising', models.FloatField(default=0.0, verbose_name=b'Probability of demand actualising')),
                ('deviation', models.FloatField(default=0.0, verbose_name=b'Deviation from recommendation')),
                ('actions', django_hstore.fields.SerializedDictionaryField(default={})),
                ('percentage_changes', django_hstore.fields.SerializedDictionaryField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='Threshold',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(default=Decimal('20.00'), verbose_name=b'Threshold amount', max_digits=6, decimal_places=2)),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name=b'Latest Update')),
            ],
        ),
    ]
