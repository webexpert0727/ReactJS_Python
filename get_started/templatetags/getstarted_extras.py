from django import template
from dateutil import parser
from datetime import datetime

register = template.Library()


@register.simple_tag
def addition(val1, val2):
    return val1 + val2


@register.filter
def convert_date(input_date):
    input_date = parser.parse(input_date)
    return datetime.strftime(input_date, "%d-%m-%Y %H:%M:%S %p")