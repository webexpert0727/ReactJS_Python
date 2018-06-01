# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from email_validator import validate_email, EmailNotValidError
from registration.forms import RegistrationForm

from django import forms
from django.utils.translation import ugettext_lazy as _

from customauth.models import MyUser

from .models import GetStartedResponse


logger = logging.getLogger('giveback_project.' + __name__)


class GetStartedResponseForm(forms.ModelForm):

    ERROR_MESSAGES = {
        'required': _('Please tell us your name'),
        'invalid': _('Please enter valid data'),

    }

    name = forms.CharField(
        label=_('Username'),
        error_messages=ERROR_MESSAGES,
    )

    class Meta:
        model = GetStartedResponse
        fields = ('name', 'email')


class CustomRegistrationForm(RegistrationForm):

    def clean_email(self):
        email = self.cleaned_data['email']
        already_exists = MyUser.objects.filter(
            email__iexact=email).exists()
        if already_exists:
            logger.warning(
                'Email is already in use: %s', email, extra={'stack': True})
            raise forms.ValidationError(_(
                'A user with this Email address already exists.'))

        try:
            email_data = validate_email(email)
            valid_email = email_data['email']  # replace with normalized form
        except EmailNotValidError:
            logger.warning('Invalid email: %s', email, exc_info=True)
            raise forms.ValidationError(_(
                'This email address is not valid. '
                'Please supply a different email address.'))
        return valid_email
