# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from braces.views import JSONResponseMixin

from django.contrib.sites.models import Site
from django.utils.decorators import method_decorator
from django.views.generic import FormView  # TemplateView

from giveback_project.helpers import geo_check

from .forms import WholesaleForm
from .models import Plan

from content.models import Review


class WholesaleView(JSONResponseMixin, FormView):
    """Wholesale."""

    form_class = WholesaleForm
    template_name = 'wholesale/wholesale.html'

    def get_context_data(self, **kwargs):
        context = super(WholesaleView, self).get_context_data(**kwargs)
        context.update({
            'plans': Plan.objects.all().order_by('the_order'),
            'current_domain': Site.objects.get_current().domain,
            'reviews': Review.objects.filter(is_workplace=True)
        })
        return context

    @method_decorator(geo_check)
    def dispatch(self, request, is_worldwide, *args, **kwargs):
        kwargs.update({'is_worldwide': is_worldwide})
        return super(WholesaleView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.send_email()
        return self.render_json_response({'success': True})

    def form_invalid(self, form):
        return self.render_json_response({'errors': form.errors})
