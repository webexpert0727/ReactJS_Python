# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _

from customauth.forms import LoginForm

from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from giveback_project.helpers import geo_check
from customauth.models import MyUser


@geo_check
def login_user(request, is_worldwide):
    logout(request)
    username = password = ''

    is_checkout = request.GET.get('checkout')

    context = {}
    form = LoginForm()
    form.fields['accesstoken'].widget = forms.HiddenInput()
    if request.POST:
        form = LoginForm(request.POST)
        form.fields['accesstoken'].widget = forms.HiddenInput()
        username = request.POST['username']
        password = request.POST['password']
        accesstoken = request.POST.get('accesstoken', '')
        user = None

        if form.is_valid():

            email = form.cleaned_data['username']
            try:
                exists = MyUser.objects.get_by_natural_key(email)
            except:
                exists = False

            if not exists:
                context['errors'] = _('Please enter a correct Email address and password. Note that both fields may be case-sensitive.')

            if accesstoken:
                user = authenticate(accesstoken=accesstoken)

                if user is None:
                    return redirect('get_started')


            else:
                user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    if is_checkout:
                        return redirect('checkout')
                    return redirect('profile')
            else:
                context['errors'] = _('Please enter a correct Email address and password. Note that both fields may be case-sensitive.')


    context['form'] = form
    context['is_worldwide'] = is_worldwide

    return render(request, 'registration/login.html/', context)
