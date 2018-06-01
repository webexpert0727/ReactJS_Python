# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import sys
from django.db import models
import requests
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)

from customers.models.facebook_customer import FacebookCustomer


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return self.get(**{'%s__iexact' % self.model.USERNAME_FIELD: username})


class MyUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='Email address',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.email

    def __str__(self):
        return self.email

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.is_admin


class FacebookBackend(object):

    def authenticate(self, accesstoken = None):

        # data from Facebook that will be pulled out, minus 'user_about_me'
        request_data = 'id'

        response = requests.get('https://graph.facebook.com/me?access_token=' + accesstoken + '&fields=' + request_data)
        # response.encoding = 'ISO-8859-1'
        # all requested user's data is here
        response_data = response.json()

        facebook_id = response_data['id']
        facebook_customer = ''
        if facebook_id is not None:
            try:
                facebook_customer = FacebookCustomer.objects.get(facebook_id = facebook_id)
                sys.stderr.write(str(facebook_customer))
                if facebook_customer is not None:
                    user = facebook_customer.customer
                    return user

            except Exception as e:
                print e
        return None

    def get_user(self, user_id):
        try:
            return MyUser.objects.get(pk=user_id)
        except MyUser.DoesNotExist:
            return None


class Login(models.Model):
    username = models.CharField("Username", max_length=32)
    password = models.CharField("Password", max_length=255)
    accesstoken = models.CharField("Access Token", max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '{} <{}>'.format(self.username)
