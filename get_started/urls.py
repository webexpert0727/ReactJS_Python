from django.conf.urls import url

from . import views, voucher
from .stripe_api import register as register_stripe

urlpatterns = [
    url(r'^$', views.index, name='get_started'),
    url(r'^recommend/$', views.recommend, name='recommend'),
    url(r'^another/$', views.another, name='another'),
    url(r'^login-existing-user$', views.login_existing_user, name='login-existing-user'),
    url(r'^login-customer$', views.login_customer, name='login-customer'),
    url(r'^register/$', views.register, name='register'),
    url(r'^register-credits/$', views.register_credits, name='register_credits'),
    url(r'^register-nespresso/$', views.register_nespresso, name='register_nespresso'),
    url(r'^register-gear/$', views.register_gear, name='register_gear'),
    url(r'^voucher/$', voucher.main, name='voucher'),
    url(r'^register/register-stripe/$', register_stripe, name='register_stripe'),
    url(r'^preregister/(?P<coffee_id>[0-9]+)/(?P<isNespresso>.*)/(?P<isOneoff>.*)/(?P<isBottled>.*)?/?$', views.preregister, name='preregister'),
    url(r'^register-worldwide/$', views.register_worldwide, name='register_worldwide'),
    url(r'^process-cart/$', views.cart_process, name='cart_process'),
    url(r'^preregister-gear/(?P<gear_id>[0-9]+)/(?P<gear_qty>[0-9]+)/(?:(?P<gear_color_id>[0-9]+)/)?$', views.preregister_gear, name='preregister_gear'),
    url(r'^substitute-subscription/$', views.substitute_subscription, name='substitute-subscription'),
    url(r'^add-subscription/$', views.add_subscription, name='add-subscription'),
]
