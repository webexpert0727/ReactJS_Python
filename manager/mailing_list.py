
from . import mailchimp_api
from . import utils
from .models import MailchimpCampaignStats


def resolveEmailId(campaign_id, email_id):
    try:
        campaignJSON = mailchimp_api.getCampaignReport(campaign_id)
        list_id = campaignJSON['recipients']['list_id']

        emailJSON = mailchimp_api.getSubscriberInfo(list_id, email_id)
        email_address = emailJSON['members'][0]['email_address']
        return email_address
    except Exception as e:
        print e
    return email_id


def processMailchimpParams(original_func):
    def new_function(*args, **kwargs):
        try:
            if args[0]:
                request = args[0]
                if 'mc_cid' in request.GET.keys() and 'mc_eid' in request.GET.keys():
                    request.session['campaign_id'] = request.GET['mc_cid']
                    request.session['campaign_email'] = resolveEmailId(request.GET['mc_cid'], request.GET['mc_eid'])
                    try:
                        MailchimpCampaignStats.objects.get(campaign_id=request.GET['mc_cid'],
                                                           email=request.session['campaign_email'])
                    except:
                        campaign = MailchimpCampaignStats.objects.get_or_create(campaign_id=request.GET['mc_cid'],
                                                                                action=MailchimpCampaignStats.NO_ACTION,
                                                                                email=request.session['campaign_email'],
                                                                                order=None)
                        campaign.save()
        except Exception as e:
            print 'error in processing mailchimp params', str(e)
        return original_func(*args, **kwargs)
    return new_function


def is_tracked(request):
    return 'campaign_id' in request.session.keys() and 'campaign_email' in request.session.keys()


def processCampaignBreakdown(campaign_id):

    result = mailchimp_api.getCampaignReport(campaign_id)
    result_summary = result['report_summary']


    #if we need to retrieve emails later then we use this
    '''
    no_view_emails = []
    open_emails = []
    click_emails = []

    result = mailchimp_api.getEmailActivity(campaign_id, count, offset)
    members = result['emails']
    for member in members:
        member_activity = member['activity']
        added = False
        if member_activity:
            if any(activity['action'] == 'open' for activity in member_activity):
                open_emails.append(member['email_address'])
                added = True
            if any(activity['action'] == 'click' for activity in member_activity):
                click_emails.append(member['email_address'])
                added = True

        if not added:
            no_view_emails.append(member['email_address'])

     no_click_emails = [email for email in open_emails if email not in click_emails]
    '''


    no_action_emails = []
    get_started_emails = []
    purchased_emails = []

    mc_stats = MailchimpCampaignStats.objects.filter(campaign_id=campaign_id)

    for mc_stat in mc_stats:
        if mc_stat.action == MailchimpCampaignStats.NO_ACTION:
            no_action_emails.append(mc_stat.email)
        elif mc_stat.action == MailchimpCampaignStats.GET_STARTED:
            get_started_emails.append(mc_stat.email)
        elif mc_stat.action == MailchimpCampaignStats.PURCHASED:
            purchased_emails.append(mc_stat.email)

    total_number = result['recipients']['recipient_count']
    result = {
        'campaign_id': campaign_id,
        'breakdown': {
            'total_number': total_number,
            'opened': {
                'number': result_summary['unique_opens'],
                'rate': result_summary['open_rate'],
                'clicked': {
                    'number': result_summary['clicks'],
                    'rate':  result_summary['click_rate'],
                    'registered': {
                        'number': len(get_started_emails),
                        'rate': get_rate(len(get_started_emails), total_number),
                        'customers': map(utils.customerEmailToCustomerDict, get_started_emails)
                    },
                    'purchased': {
                        'number': len(purchased_emails),
                        'rate': get_rate(len(purchased_emails), total_number),
                        'customers': map(utils.customerEmailToCustomerDict, purchased_emails)
                    },
                    'no_action_after_click': {
                        'number': len(no_action_emails),
                        'rate': get_rate(len(no_action_emails), total_number),
                        'customers': map(utils.customerEmailToCustomerDict, no_action_emails)
                    },
                },
                'not_clicked': {
                    'number':  result_summary['unique_opens'] - result_summary['clicks'],
                    'rate': get_rate(result_summary['unique_opens'] - result_summary['clicks'], total_number),
                }
            },
            'not_opened': {
                'number': total_number - result_summary['unique_opens'],
                'rate': get_rate(total_number - result_summary['unique_opens'], total_number),
            }

        }
    }

    return result


def get_rate(numerator, denominator):
    if denominator == 0:
        return 0
    else:
        return float(numerator) / denominator


def update_mailchimp_tracking(request, order, action):
    try:
        if is_tracked(request):
            campaign_id = request.session['campaign_id']
            if 'campaign_email' in request.session.keys() and request.session['campaign_email']:
                email = request.session['campaign_email']
            elif order:
                email = order.customer.get_email()
            existing_stats = MailchimpCampaignStats.objects.get(campaign_id=campaign_id, email=email)
            existing_stats.action = action
            existing_stats.order = order
            existing_stats.save()
            if action == MailchimpCampaignStats.PURCHASED:
                request.session['campaign_email'] = ''
                request.session['campaign_id'] = ''
    except Exception as e:
        print e
