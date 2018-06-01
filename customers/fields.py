# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core.validators import validate_email
from django.forms.widgets import SelectMultiple
from django.utils.encoding import force_text


class CommaSeparatedEmailField(forms.CharField):
    def to_python(self, value):
        value = super(CommaSeparatedEmailField, self).to_python(value)
        if not value:
            return []
        self.run_validators(value)  # run validators while it's just a string
        contacts = {email.strip().lower(): '' for email in value.split(',')}
        return list(contacts.items())

    def clean(self, value):
        def is_valid(email):
            try:
                validate_email(email)
            except forms.ValidationError:
                return False
            return True
        value = super(CommaSeparatedEmailField, self).clean(value)
        value = [(email, name) for email, name in value if is_valid(email)]
        return value


class GoogleContactField(CommaSeparatedEmailField):
    widget = SelectMultiple

    def to_python(self, value):
        if not value or not isinstance(value, list):
            return []
        contacts = {}
        for contact in value:
            name, email = force_text(contact).split(':')
            contacts[email.strip().lower()] = name.strip().title()
        return list(contacts.items())
