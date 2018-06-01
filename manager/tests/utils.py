# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import re

from django.test.client import Client
from django.utils.functional import curry


JSON_CONTENT_TYPE_RE = re.compile('^application\\/(vnd\\..+\\+)?json')


class JSONClient(Client):

    def request(self, **request):
        response = super(JSONClient, self).request(**request)
        response.json = curry(self._parse_json, response)
        return response

    def post(self, path, data=None, content_type='application/json',
             follow=False, secure=False, **extra):
        """Request a response from the server using POST."""
        return super(JSONClient, self).post(
            path, data=json.dumps(data),
            content_type=content_type, secure=secure, **extra)

    def _parse_json(self, response, **extra):
        if not hasattr(response, '_json'):
            if not JSON_CONTENT_TYPE_RE.match(response.get('Content-Type')):
                raise ValueError(
                    'Content-Type header is "{0}", not "application/json"'
                    .format(response.get('Content-Type')))
            response._json = json.loads(response.content.decode(), **extra)
        return response._json
