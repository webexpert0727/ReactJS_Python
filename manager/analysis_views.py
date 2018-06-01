# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from datetime import datetime

from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST

from . import analysis_api
from .authentication import adminOnly


@adminOnly
@require_POST
def updateReportCard(request):

    data = json.loads(request.body)

    report_id = data['report_id']
    facebook_advertising_cost = data['facebook_advertising_cost']
    blog_posts = data['blog_posts']
    email_campaigns = data['email_campaigns']
    adwords_cost = data['adwords_cost']
    roadshows = data['roadshows']
    new_coffees = data['new_coffees']

    RESULT_JSON = analysis_api.processUpdateReportCard(report_id, facebook_advertising_cost, blog_posts, email_campaigns, adwords_cost, roadshows, new_coffees)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@adminOnly
@require_GET
def getReportCard(request):

    start_date_str = request.GET['start_date']
    end_date_str = request.GET['end_date']

    start_date = datetime.strptime(start_date_str, '%d-%m-%Y').date()
    end_date = datetime.strptime(end_date_str, "%d-%m-%Y").date()

    RESULT_JSON = analysis_api.processGetReportCard(start_date, end_date)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@adminOnly
@require_POST
def saveRecommendation(request):

    data = json.loads(request.body)

    facebook_advertising_cost = data['facebook_advertising_cost']
    blog_posts = data['blog_posts']
    email_campaigns = data['email_campaigns']
    adwords_cost = data['adwords_cost']
    roadshows = data['roadshows']
    new_coffees = data['new_coffees']

    expected_demand = data['expected_demand']
    demand_actualising = data['demand_actualising']

    RESULT_JSON = analysis_api.processSaveRecommendation(facebook_advertising_cost, adwords_cost, new_coffees, email_campaigns, roadshows, blog_posts, expected_demand, demand_actualising)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@adminOnly
@require_GET
def getRecommendation(request):

    RESULT_JSON = analysis_api.processGetRecommendation()

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@adminOnly
@require_GET
def getCustomerSegments(request):

    RESULT_JSON = analysis_api.processGetCustomerSegments()

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')
