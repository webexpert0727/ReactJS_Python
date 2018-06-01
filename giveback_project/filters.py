# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.conf import settings


# def skip_unreadable_post(record):
#     print 'record:'. record
#     print 'record.exc_info:', record.exc_info
#     if record.exc_info:
#         exc_type, exc_value = record.exc_info[:2]
#         if isinstance(exc_value, UnreadablePostError):
#             return False
#     return True


class FilterIgnorable404URLs(logging.Filter):
    def filter(self, record):
        # request = record.request

        # print 'record:', type(record), record
        # print 'dir(record)', dir(record)
        # print 'record.exc_info:', record.exc_info
        # print 'record.exc_text:', record.exc_text
        # print 'record.message:', type(record.message), record.message
        # print 'module:', type(record.module), record.module
        # print 'msg:', type(record.msg), record.msg
        # print 'name:', type(record.name), record.name
        if hasattr(record, 'status_code') and record.status_code != 404:
            return True
        request = getattr(record, 'request', False)
        # print 'request:', request
        if request:
            path = request.get_full_path()
            # print 'path:', path
        # path = record.request.get_full_path()
        # if getattr(settings, 'IGNORABLE_404_URLS'):
        #     is_ignorable = any(
        #         pattern.search(path)
        #         for pattern in settings.IGNORABLE_404_URLS)
        #     if is_ignorable:
        #         return False
        return True


    # def __init__(self, callback):
    #     self.callback = callback

    # def filter(self, record):
    #     if self.callback(record):
    #         return 1
    #     return 0
