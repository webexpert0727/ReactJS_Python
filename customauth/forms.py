# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _


class LoginForm(forms.Form):

    ERROR_MESSAGES = {
        'requiredUsername': _('Email is required!'),
        'requiredPassword': _('Password is required!'),
        'invalid': _('Please enter valid data'),

    }

    username = forms.EmailField(
        label=_('username'),
        required=False,
    )
    password = forms.CharField(
        label=_('password'),
        widget=forms.PasswordInput,
        required=False,
    )
    accesstoken = forms.CharField(
        label='accesstoken',
        required=False,
    )

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        accesstoken = cleaned_data.get("accesstoken")

        if accesstoken:
            pass
        else:
            if not username:
                self.add_error('username', self.ERROR_MESSAGES['requiredUsername'])
            if not password:
                self.add_error('password', self.ERROR_MESSAGES['requiredPassword'])
