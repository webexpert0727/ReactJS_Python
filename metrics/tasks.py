# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from functools import partial

from celery.schedules import crontab
from celery.task import periodic_task

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError

from requests.exceptions import RequestException

from django.conf import settings

from giveback_project import celery_app

from .services import business, application
from .services.utils import cohort_analysis, app_data


logger = logging.getLogger('giveback_project.' + __name__)

client = InfluxDBClient(
    settings.INFLUXDB_HOST, settings.INFLUXDB_PORT,
    settings.INFLUXDB_USER, settings.INFLUXDB_PASSWORD,
    settings.INFLUXDB_APP_DB)


@celery_app.task(ignore_result=True)
def send_metric(metric, **kwargs):
    if not settings.INFLUXDB_HOST:
        return
    func = getattr(application, metric)
    func = partial(func, **kwargs)
    write_data(app_data(func, metric))


@periodic_task(run_every=(crontab(minute=0, hour=3)))
def sync_metrics(sync_all=False):
    if not settings.INFLUXDB_HOST:
        return

    base_metrics = [
        business.revenue_churn_rate,
        business.customer_churn_rate,
        business.customer_churn_rate_non_strict,
        business.customer_retention_rate,
        business.customer_retention_rate_non_strict,
        business.customer_cumulative_lifetime_value,
        business.customer_lifetime_value,
    ]
    for func in base_metrics:
        write_data(cohort_analysis(func))

    mrr_metrics = [
        business.monthly_recurring_revenue,
        business.new_monthly_recurring_revenue,
        business.expansion_monthly_recurring_revenue,
        business.churn_monthly_recurring_revenue,
        business.net_new_monthly_recurring_revenue,
    ]
    for func in mrr_metrics:
        write_data(app_data(func, 'mrr'))

    app_metrics = [
        application.k_factor,
    ]

    if sync_all:
        app_metrics.extend([
            application.customers,
            application.orders,
            application.gear_orders,
            application.events,
            application.invites,
        ])

    for func in app_metrics:
        write_data(app_data(func, func.__name__))


def write_data(data):
    try:
        client.write_points(data, time_precision='u', batch_size=100)
    except (RequestException, InfluxDBClientError, InfluxDBServerError):
        logger.error('Failed to send metrics to InfluxDB', exc_info=True)
        raise
