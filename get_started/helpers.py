import random
import string
from django.utils import timezone
from customers.models import Order
from coffees.models import BrewMethod, CoffeeGear


def generate_securerandompass(n):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(n))


def createOrder(p_customer, p_coffee, p_shipping_date, p_price, p_preferences,  p_is_recurrent, p_brew_method, p_voucher, p_package, is_nespresso):
    order = None
    different = p_preferences.different if p_preferences else False
    interval = p_preferences.interval if p_preferences else 14
    if is_nespresso:
        order = Order(
            customer = p_customer,
            coffee = p_coffee,
            date = timezone.now(),
            shipping_date = p_shipping_date,
            amount = p_price,
            interval = interval,
            recurrent = p_is_recurrent,
            status = Order.ACTIVE,
            brew = BrewMethod.objects.get(name_en='Nespresso'),
            different = different,
            voucher = p_voucher,
            package=p_package
        )

    else:
        order = Order(
            customer=p_customer,
            coffee=p_coffee,
            date=timezone.now(),
            shipping_date=p_shipping_date,
            amount=p_price,
            interval=interval,
            recurrent=p_is_recurrent,
            status=Order.ACTIVE,
            brew=p_brew_method,
            different=different,
            voucher=p_voucher,
            package=p_package
        )

    return order


def vouchers_allowed(item):
    """Check if voucher allowed
    """
    FORBIDDEN_COFFEE_IDS = []
    FORBIDDEN_GEAR_IDS = list(CoffeeGear.objects.filter(special='christmas').values_list('id', flat=True))

    if isinstance(item, dict):
        if item.get('coffee'):
            if item.get('coffee').get('id') in FORBIDDEN_COFFEE_IDS:
                return False
        elif item.get('gear'):
            if item.get('gear').get('id') in FORBIDDEN_GEAR_IDS:
                return False

    return True
