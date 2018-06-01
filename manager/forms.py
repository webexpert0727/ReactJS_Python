# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from customauth.models import MyUser


class ManagerLoginForm(AuthenticationForm):

    class Meta:
        model = MyUser

    def clean(self):
        cleaned_data = super(ManagerLoginForm, self).clean()
        rememberme = self.data['rememberme']
        if rememberme:
            # expires in 6 months
            self.request.session.set_expiry(60 * 60 * 24 * 30 * 6)
        else:
            self.request.session.set_expiry(0)
        return cleaned_data

    def confirm_login_allowed(self, user):
        super(ManagerLoginForm, self).confirm_login_allowed(user)
        if not user.groups.filter(name__in=['admin', 'packer']).exists():
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name})
