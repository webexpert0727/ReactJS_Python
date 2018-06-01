import requests
from giveback_project.settings import base
import json

def getMailchimpLists(count, offset):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/lists?count=%s?offset=%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, count, offset))
    r = r.json()

    return r

def getMailchimpListMembers(list_id, count, offset):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/lists/%s/members?count=%s?offset=%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, list_id, count, offset))
    r = r.json()

    return r


def formOperationsListDeleteMembers(list_id, members_ids):
    operations = []

    for id in members_ids:
        operation_details = {
            "method": "DELETE",
            "path": "lists/%s/members/%s" % (list_id, id),
        }
        operations.append(operation_details)

    return operations

def formOperationsListsMembers(list_id, emails):
    operations = []

    for email in emails:
        operation_details = {
            "method": "POST",
            "path": "lists/%s/members" % list_id,
            "body": json.dumps({
                "status": "subscribed",
                "email_address": email
            })
        }
        operations.append(operation_details)

    return operations

def batch(json_body):
    r = requests.post("https://%s:%s@us12.api.mailchimp.com/3.0/batches" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY), json=json_body)
    return r.json()

def getMailchimpCampaigns(count, offset):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/campaigns?count=%s?offset=%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, count, offset))
    r = r.json()

    return r

def createMailchimpList(json_body):
    r = requests.post("https://%s:%s@us12.api.mailchimp.com/3.0/lists" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY), json=json_body)
    return r.json()

def getCampaignReport(campaign_id):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/campaigns/%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, campaign_id))
    return r.json()

def getSubscriberInfo(list_id, email_id):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/lists/%s/members?unique_email_id=%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, list_id, email_id))
    return r.json()


def getEmailActivity(campaign_id, count, offset):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/reports/%s/email-activity?count=%s?offset=%s?" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, campaign_id, count, offset))
    return r.json()

def getCampaignURLIDs(campaign_id, count, offset):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/reports/%s/click-details?count=%s?offset=%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, campaign_id, count, offset))
    r = r.json()
    urls_clicked = r['urls_clicked']

    url_ids = []

    for details in urls_clicked:
        url_ids.append(details['id'])

    return url_ids

def getClickerDetails(campaign_id, link_id, count, offset):
    r = requests.get("https://%s:%s@us12.api.mailchimp.com/3.0/reports/%s/click-details/%s/members?count=%s?offset=%s" % (base.MAILCHIMP_USERNAME, base.MAILCHIMP_API_KEY, campaign_id, link_id, count, offset))
    return r.json()
