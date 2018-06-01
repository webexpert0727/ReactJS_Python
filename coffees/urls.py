# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf.urls import url

from .views import *
from .vouchers import stripe_send_friend

urlpatterns = [
    url(r'^$', bags, name='coffees'),
    url(r'^shotpods$', pods, name='nespresso'),
    url(r'^send-friend$', send_friend, name='send-friend'),
    url(r'^shop-gift$', CoffeeGearListView.as_view(), name='shop-gift'),
    url(r'^shop-gift-set$', CoffeeGearSetListView.as_view(), name='shop-gift-set'),
    url(r'^gift-sets-voucher$', gift_sets_voucher, name='gift-sets-voucher'),
    url(r'^buy-gear/$', buy_gear, name='buy_gear'),
    url(r'^(?P<coffee_id>[0-9]+)/$', detail, name='detail'),
    url(r'^stripe_send_friend/$', stripe_send_friend, name='stripe_send_friend'),
    url(r'^set_stripe_credits/$', set_stripe_credits, name='set_stripe_credits'),
    url(r'^shared/$', shared_sticker, name='shared_sticker'),
    url(r'^cart_add/$', cart_add, name='cart_add'),
    url(r'^checkout/$', checkout, name='checkout'),
    url(r'^get_shipping_rates/$', get_shipping_rates, name='get_shipping_rates'),
    url(r'^cart_confirm/$', cart_confirm, name='cart_confirm')
]
