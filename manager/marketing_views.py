# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import re
from datetime import datetime

from jsonview.decorators import json_view

from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST

from customers.models import Customer

from . import mailchimp_api
from . import mailchimp_config
from . import mailing_list
from . import utils


@require_GET
def get_all_active_customers(request):
    customers = list(Customer.objects.active())
    if customers:
        status = 200
        result = {
            "status": status,
            "customers": utils.customer_json(customers)
        }
    else:
        status = 500
        err = "No customers are found matching the given criteria"
        result = {
            "status": status,
            "error_message": err
        }

    return HttpResponse(json.dumps(result), content_type='application/json')


@require_GET
def get_all_inactive_customers(request):
    from_date = request.GET.get('fromdate')
    if from_date:
        from_date = datetime.strptime(from_date, '%d-%m-%Y').date()
        customers = list(Customer.objects.inactive(from_date=from_date))
    else:
        customers = list(Customer.objects.inactive())

    if customers:
        result = {'status': 200,
                  'customers': utils.customer_json(customers)}
    else:
        result = {'status': 500,
                  'error_message': ('No customers are found matching'
                                    'the given criteria')}
    return HttpResponse(json.dumps(result), content_type='application/json')


@require_GET
def getMailchimpLists(request):
    RESULT_JSON = {}
    errors = []
    lists = []
    count = request.GET['count']
    offset = request.GET['offset']

    try:
        result = mailchimp_api.getMailchimpLists(count, offset)
        lists_set = result['lists']

        for list in lists_set:
            list_details = {}
            list_details['list_id'] = list['id']
            list_details['list_name'] = list['name']
            list_details['stats'] = list['stats']
            lists.append(list_details)

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['error_message'] = errors
        RESULT_JSON['status'] = 500
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    RESULT_JSON['status'] = 200
    RESULT_JSON['total_items'] = result['total_items']
    RESULT_JSON['lists'] = lists

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_POST
def addEmailsToList(request):
    data = json.loads(request.body)
    RESULT_JSON = {}
    list_id = data['list_id']
    emails = data['emails']

    try:
        json_body = {}
        operations = mailchimp_api.formOperationsListsMembers(list_id, emails)

        json_body['operations'] = operations

        r = mailchimp_api.batch(json_body)
        RESULT_JSON['status'] = 200
        RESULT_JSON['message'] = 'Success'

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    except Exception as e:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = r['details']
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def getMailchimpCampaigns(request):
    RESULT_JSON = {}
    errors = []
    campaigns = []
    count = request.GET['count']
    offset = request.GET['offset']

    try:
        result = mailchimp_api.getMailchimpCampaigns(count, offset)
        campaigns_set = result['campaigns']

        for campaign in campaigns_set:
            campaign_details = {}
            campaign_details['campaign_id'] = campaign['id']
            campaign_details['type'] = campaign['type']
            campaign_details['status'] = campaign['status']
            campaign_details['emails_sent'] = campaign['emails_sent']
            campaign_details['recipients'] = campaign['recipients']
            campaign_details['settings'] = campaign['settings']

            try:
                campaign_details['report_summary'] = campaign['report_summary']
            except KeyError as e:
                pass

            campaigns.append(campaign_details)

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['error_message'] = errors
        RESULT_JSON['status'] = 500
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    RESULT_JSON['status'] = 200
    RESULT_JSON['total_items'] = result['total_items']
    RESULT_JSON['campaigns'] = campaigns

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_POST
def createMailchimpList(request):
    try:
        data = json.loads(request.body)

        # for testing
        # data = {
        #     'list_name' : 'IPMAN_TEST',
        #     'permission_reminder' : 'random block of strings',
        #     'from_name' : 'Keefe Tan',
        #     'from_email' : 'keefetan21@gmail.com',
        # }

        RESULT_JSON = {}
        errors = []
        json_body = {}

        json_body['name'] = data['list_name']
        json_body['contact'] = mailchimp_config.HOOK_COFFEE_CONTACT
        json_body['permission_reminder'] = data['permission_reminder']

        email = data['from_email']

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            RESULT_JSON['error_message'] = 'Please input a valid email'
            RESULT_JSON['status'] = 500

            return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

        json_body['campaign_defaults'] = {
            'from_name': data['from_name'],
            'from_email': email,
            'subject': '',
            'language': 'English'
        }
        json_body['email_type_option'] = mailchimp_config.HOOK_COFFEE_EMAIL_TYPE_OPTION

        try:
            result = mailchimp_api.createMailchimpList(json_body)
            RESULT_JSON['status'] = 200
            RESULT_JSON['message'] = 'List has been successfully created'
        except Exception as e:
            RESULT_JSON['error_message'] = result['detail']
            RESULT_JSON['status'] = 500

        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['error_message'] = errors
        RESULT_JSON['status'] = 500
        return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@json_view
def retrieveCampaignBreakdown(request):
    if 'campaign_id' in request.GET.keys():
        campaign_id = request.GET['campaign_id']
    else:
        return {
                   "status": 500,
                   "error_message": "campaign_id not found"
        }

    return mailing_list.processCampaignBreakdown(campaign_id)


@require_GET
def getCampaignReport(request):
    RESULT_JSON = {}

    campaign_id = request.GET['campaign_id']

    result = mailchimp_api.getCampaignReport(campaign_id)

    if result['status'] == 404:
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = 'No campaign was found'

    else:
        
        try:
            RESULT_JSON['report_summary'] = result['report_summary']
            RESULT_JSON['status'] = 200
        except KeyError as e:
            RESULT_JSON['error_message'] = 'No report available'
            RESULT_JSON['status'] = 500

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def getOpenedCampaignEmails(request):
    RESULT_JSON = {}
    errors = []
    emails = []

    try:
        campaign_id = request.GET['campaign_id']
        count = request.GET['count']
        offset = request.GET['offset']

        result = mailchimp_api.getEmailActivity(campaign_id, count, offset)

        members = result['emails']

        for member in members:
            member_activity = member['activity']

            if member_activity:
                if any(activity['action'] == 'open' for activity in member_activity):
                    emails.append(member['email_address'])

        RESULT_JSON['emails'] = emails
        RESULT_JSON['status'] = 200

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_GET
def getClickedCampaignEmails(request):
    RESULT_JSON = {}
    errors = []
    emails = []

    try:
        campaign_id = request.GET['campaign_id']
        count = request.GET['count']
        offset = request.GET['offset']

        url_ids = mailchimp_api.getCampaignURLIDs(campaign_id, 9999, 0) #count & offset hard coded

        for id in url_ids:
            result = mailchimp_api.getClickerDetails(campaign_id, id, count, offset)
            members = result['members']

            for member in members:
                email = member['email_address']

                if email not in emails:
                    emails.append(email)

        RESULT_JSON['emails'] = emails
        RESULT_JSON['status'] = 200

    except Exception as e:
        errors.append(str(e))
        RESULT_JSON['status'] = 500
        RESULT_JSON['error_message'] = errors

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')
