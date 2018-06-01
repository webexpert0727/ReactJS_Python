from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

import raven
from raven.contrib.celery import register_logger_signal, register_signal

from django.conf import settings  # noqa

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giveback_project.settings.live')


class CustomCelery(Celery):

    def on_configure(self):
        dsn = settings.RAVEN_CONFIG.get('dsn')
        if dsn:
            client = raven.Client(dsn)

            # register a custom filter to filter out duplicate logs
            register_logger_signal(client)

            # hook into the Celery error handler
            register_signal(client)

app = CustomCelery('giveback_project')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks()
