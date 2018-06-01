from django.db.models import Q
from manager.models import IntercomLocal


def get_number_unsubscribed(month, year):
    return IntercomLocal.objects.filter(
        event="canceled-subscription",
        added_timestamp__month=month,
        added_timestamp__year=year
    ).count()


def get_number_new_subscribers(month, year):
    return IntercomLocal.objects.filter(Q(
        event="created-subscription",
        added_timestamp__month=month,
        added_timestamp__year=year) | Q(
        event="created-one-off",
        added_timestamp__month=month,
        added_timestamp__year=year)
    ).count()
