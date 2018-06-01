# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def top_bar(request):
    from content.models import TopBar

    context = {'top_bar': {'visible': False}}

    if 'register' in request.get_full_path():
        pass
    else:
        try:
            context['top_bar'] = TopBar.objects.latest('id')
        except TopBar.DoesNotExist:
            pass
    return context
