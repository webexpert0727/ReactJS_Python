# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Postcard(models.Model):
    customer_postcard = models.FileField(upload_to='postcards/')
