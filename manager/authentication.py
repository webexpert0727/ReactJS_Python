# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http import HttpResponse

from customauth.models import MyUser


def authenticateAdmin(user):
    if user is None or not user.is_admin:
        return False
    else:
        return True


def authenticatePacker(user):
    if user is None or not user.groups.filter(name='packer').exists():
        return False
    else:
        return True


def failAuthentication():
    RESULT_JSON = {}

    RESULT_JSON['status'] = 403
    RESULT_JSON['error_message'] = "Forbidden"

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


# decorator for sensitive data
def adminOnly(f):
    def wrap(request, *args, **kwargs):
        # this check the session if userid key exist, if not it will redirect to login page
        try:
            userId = request.session['user']
            user = MyUser.objects.get(id=userId)

            if authenticateAdmin(user):
                return f(request, *args, **kwargs)
            else:
                return failAuthentication()

        except KeyError:
            return failAuthentication()
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
