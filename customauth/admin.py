# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import ugettext_lazy as _

from customauth.models import MyUser


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_('Password confirmation'),
        widget=forms.PasswordInput)

    class Meta:
        model = MyUser
        fields = ('email',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput,
        required=False)
    password2 = forms.CharField(
        label=_('Password confirmation'),
        widget=forms.PasswordInput,
        required=False)

    class Meta:
        model = MyUser
        fields = ('email', 'password')

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if (password1 or password2) and (password1 != password2):
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def save(self, commit=True):
        user = super(UserChangeForm, self).save(commit=False)
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2:
            user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'is_admin')
    list_filter = ('is_admin',)
    default_filters = ('is_admin__exact=1',)

    fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
        ('Permissions', {'fields': ('is_admin', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('is_admin',)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'action_time', 'user', 'content_type', 'object_id',
        'object_repr', 'action_flag', 'change_message')
    list_filter = ('content_type',)
    search_fields = ('user__email',)
    date_hierarchy = 'action_time'

admin.site.register(MyUser, UserAdmin)
