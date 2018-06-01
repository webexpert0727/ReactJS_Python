# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _


BUSINESS_CHOICES = (
    ('office', _('Office')),
    ('restaurant', _('Restaurant')),
    ('bar/pub', _('Bar/Pub')),
    ('other', _('Other'))
)


class WholesaleForm(forms.Form):

    name = forms.CharField(max_length=128)
    company_name = forms.CharField(max_length=128)
    email = forms.EmailField()
    contact_number = forms.CharField(max_length=128)
    business = forms.ChoiceField(choices=BUSINESS_CHOICES,
                                 widget=forms.RadioSelect)
    comment = forms.CharField(
        max_length=2048,
        label=_('How can we help?'),
        widget=forms.Textarea(attrs={'rows': 3}))

    def send_email(self):
        html_content = '''
            <p><strong>Name:</strong> %(name)s</p>
            <p><strong>Company Name:</strong> %(company_name)s</p>
            <p><strong>Email:</strong> %(email)s</p>
            <p><strong>Contact Number:</strong> %(contact_number)s.</p>
            <p><strong>Type of Business:</strong> %(business)s.</p>
            <p><strong>Comment:</strong> %(comment)s.</p>
        ''' % self.cleaned_data

        msg = EmailMessage(
            subject='[Wholesale] %(name)s | %(company_name)s' % self.cleaned_data,
            body=html_content,
            to=['hola@hookcoffee.com.sg'],
            from_email='Hook Coffee <system@hookcoffee.com.sg>'
        )
        msg.content_subtype = 'html'
        msg.send()
