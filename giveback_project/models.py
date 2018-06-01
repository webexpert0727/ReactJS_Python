# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from registration.backends.simple.views import RegistrationView

from customers.models import Customer


class MyRegistrationView(RegistrationView):

    def register(self, request, form):

        user = super(MyRegistrationView, self).register(request, form)

        Customer.objects.create(
            user=user,
            email=form.cleaned_data['email']
        )
        return user

    def get_success_url(self, request, user):
        return reverse('profile')

