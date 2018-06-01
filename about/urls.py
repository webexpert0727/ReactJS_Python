from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='about'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^academy/$', views.hookcoffee_academy, name='hookcoffee_academy'),
]
