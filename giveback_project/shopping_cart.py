# -*- coding: utf-8 -*-

import json
import logging

from django.views.decorators.http import require_POST
from jsonview.decorators import json_view
from coffees.models import CoffeeType as Coffee, BrewMethod, CoffeeGear, WorkShops
from customers.models import ShoppingCart, Customer, Preferences

logger = logging.getLogger('giveback_project.' + __name__)


@require_POST
@json_view
def load_cart(request):
    # request.session['shopping-cart'] = [] # uncomment to erase the cart
    return request.session.get('shopping-cart', [])


@require_POST
@json_view
def update_cart(request):
    # WARNING: request.body is a string, not json
    cart_json = json.loads(request.body) or []
    cart_str = json.dumps(request.body) or ""
    request.session['shopping-cart'] = cart_json

    if hasattr(request.user, "customer"):
        customer = request.user.customer
        premanent_cart, created = ShoppingCart.objects.get_or_create(customer=customer)
        premanent_cart.content = request.body
        premanent_cart.save()

    return cart_json


@require_POST
@json_view
def add_bags(request):
    cart = json.loads(request.body) or []

    try:
        coffee = Coffee.objects.get(id=cart.get('coffee_id'))
        brew = BrewMethod.objects.get(id=cart.get('brew_id'))
        qty = int(cart.get('qty'))
    except Coffee.DoesNotExist:
        return None
    except BrewMethod.DoesNotExist:
        return None
    except ValueError:
        qty = 1
    except Exception as e:
        logger.debug('shopping_cart add_bags() cart={}, error:{}'.format(
            cart, e))
        return None

    return {
        'coffee_id': coffee.id,
        'name': coffee.name,
        'price': coffee.amount_one_off,
        'brew_id': brew.id,
        'brew': brew.name,
        'package': cart.get('package_id'),
        'qty': qty,
    }


@require_POST
@json_view
def add_course(request):
    cart = json.loads(request.body) or []
    try:
        course = WorkShops.objects.get(id=cart.get('course_id'))
        qty = int(cart.get('qty'))
        # course_schedule, created = CustomerWorkshops.objects.get_or_create(user=request.user,
        #                 workshop = course,
        #                 scheduled_date = cart.get("date"))
        # print cart
        print request.user
    except course.DoesNotExist:
        return None
    except ValueError:
        qty = 1
    except Exception as e:
        logger.debug('Error While adding course add_courses() cart={}, error:{}'.format(
            cart, e))
        return None

    return {
        'course_id': course.id,
        'name': course.name,
        'price': course.cost,
        'qty': qty,
        'date': cart.get("date")
    }


@require_POST
@json_view
def add_pods(request):
    cart = json.loads(request.body) or []
    try:
        coffee = Coffee.objects.get(id=cart.get('coffee_id'))
        qty = int(cart.get('qty'))
    except Coffee.DoesNotExist:
        return None
    except ValueError:
        qty = 1
    except Exception as e:
        logger.debug('shopping_cart add_pods() cart={}, error:{}'.format(
            cart, e))
        return None

    brew = BrewMethod.objects.get(name='Nespresso')

    return {
        'coffee_id': coffee.id,
        'name': coffee.name,
        'price': coffee.amount_one_off,
        'qty': qty,
        'brew_id': brew.id,
    }

@require_POST
@json_view
def add_gear(request):
    cart = json.loads(request.body) or []
    try:
        gear = CoffeeGear.objects.get(id=cart.get('gear_id'))
        qty = int(cart.get('qty'))
    except CoffeeGear.DoesNotExist:
        return None
    except ValueError:
        qty = 1
    except Exception as e:
        logger.debug('shopping_cart add_gear() cart={}, error:{}'.format(
            cart, e))
        return None

    return {
        'gear_id': gear.id,
        'name': gear.name,
        'price': gear.price,
        'qty': qty,
    }

@require_POST
@json_view
def add_bottled(request):
    cart = json.loads(request.body) or []

    try:
        coffee = Coffee.objects.get(id=cart.get('coffee_id'))
        brew = BrewMethod.objects.get(name_en="Cold Brew")
        qty = int(cart.get('qty'))
    except Coffee.DoesNotExist:
        return None
    except BrewMethod.DoesNotExist:
        return None
    except ValueError:
        qty = 1
    except Exception as e:
        logger.debug('shopping_cart add_bags() cart={}, error:{}'.format(
            cart, e))
        return None

    temp = {
        'coffee_id': coffee.id,
        'name': coffee.name,
        'price': coffee.amount_one_off,
        'brew_id': brew.id,
        'brew': brew.name,
        'package': Preferences.BOTTLED,
        'qty': qty,
    }
    return temp
