# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.decorators.cache import cache_page
from django.views.generic import View

from braces.views import (
    GroupRequiredMixin, JSONResponseMixin, JsonRequestResponseMixin)


class BaseApiView(GroupRequiredMixin, JsonRequestResponseMixin,
                  JSONResponseMixin, View):
    """Base [Manager] API view."""

    # PermissionRequiredMixin: permission_required = 'manager.can_view_pack'
    # require_json = True
    group_required = ('admin', 'packer')

    def no_permissions_fail(self, request=None):
        return self.render_json_response({'error_message': 'Forbidden'}, 403)

    # def render_json_response(self, context_dict, status=200):
    #     Monkey patching ;)
    #     resp = super(ApiView, self).render_json_response(context_dict, status)
    #     error = context_dict.get('error') if isinstance(context_dict, dict) else None
    #     if error:
    #         resp.reason_phrase = error
    #     return resp


class CacheMixin(object):
    cache_timeout = 60 * 60  # hour

    # def dispatch(self, *args, **kwargs):
    #     return cache_page(self.cache_timeout)(
    #         super(CacheMixin, self).dispatch)(*args, **kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        return cache_page(cls.cache_timeout)(
            super(CacheMixin, cls).as_view(**initkwargs))
