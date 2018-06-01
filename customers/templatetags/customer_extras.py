from django import template

from giveback_project.helpers import get_estimated_date as get_estimated_date_original
from datetime import timedelta

register = template.Library()


@register.simple_tag
def subtract(val1, val2):
    return val1 - val2


@register.simple_tag
def get_estimated_date(shipping_date):
    return get_estimated_date_original(shipping_date)
