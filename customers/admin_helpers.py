import logging
logger = logging.getLogger(__name__)


def export_csv_customer(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=mymodel.csv'

    if not request.user.has_perm('customers.export_customer'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    writer.writerow([
        smart_str(u"id"),
        smart_str(u"user"),
        smart_str(u"customer"),
        smart_str(u"address"),
        smart_str(u"postcode"),
        smart_str(u"phone"),
        smart_str(u"amount"),
        smart_str(u"vouchers"),
        smart_str(u"orders"),
        smart_str(u"stripe_id"),
        smart_str(u"card_details"),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.user),
            smart_str(obj.get_full_name()),
            smart_str(obj.get_full_address()),
            smart_str(obj.postcode),
            smart_str(obj.phone),
            smart_str(obj.amount),
            smart_str(obj.get_all_vouchers()),
            smart_str(obj.get_count_orders()),
            smart_str(obj.stripe_id),
            smart_str(obj.card_details),
        ])
    return response
export_csv_customer.short_description = u"Export CSV"


def export_csv_customer_intercom(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=for_intercom.csv'

    if not request.user.has_perm('customers.export_customer'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    writer.writerow([
        smart_str(u'user_id'),
        smart_str(u'email'),
        smart_str(u'name'),
        smart_str(u'signed_up_at'),
        smart_str(u'last_login_at'),
        smart_str(u'last_order_at'),
        smart_str(u'paused'),
        smart_str(u'unsubscribed'),
        smart_str(u'has_active_order'),
        smart_str(u'address'),
        smart_str(u'postcode'),
        smart_str(u'phone'),
        smart_str(u'vouchers'),
        smart_str(u'total_spend'),
        smart_str(u'shipped_orders'),
        smart_str(u'facebook_id'),
        smart_str(u'stripe_id'),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.user.email),
            smart_str(obj.get_full_name()),
            smart_str(obj.get_signed_up()),
            smart_str(obj.get_last_login()),
            smart_str(obj.get_last_order_date()),
            smart_str(obj.subscription_is_paused()),
            smart_str(obj.subscription_is_canceled()),
            smart_str(obj.has_active_order()),
            smart_str(obj.get_full_address()),
            smart_str(obj.postcode),
            smart_str(obj.phone),
            smart_str(obj.get_all_voucher_names()),
            smart_str(obj.get_total_spend()),
            smart_str(obj.get_count_orders()),
            smart_str(obj.get_facebook_id()),
            smart_str(obj.stripe_id),
        ])
    return response
export_csv_customer_intercom.short_description = u"Export additional information about customers"


def sync_intercom_tags(modeladmin, request, queryset):
    from customers.tasks import sync_tags
    sync_tags.delay()


def export_csv_preferences(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=mymodel.csv'

    if not request.user.has_perm('customers.export_preferences'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    writer.writerow([
        smart_str(u"id"),
        smart_str(u"customer"),
        smart_str(u"coffee"),
        smart_str(u"flavor"),
        smart_str(u"brew"),
        smart_str(u"package"),
        smart_str(u"different"),
        smart_str(u"intense"),
        smart_str(u"interval"),
    ])
    for obj in queryset:
        flavors = ' | '.join([str(v) for v in obj.flavor.all()])
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.customer),
            smart_str(obj.coffee),
            smart_str(flavors),
            smart_str(obj.brew),
            smart_str(obj.package),
            smart_str(obj.different),
            smart_str(obj.intense),
            smart_str(obj.interval),
        ])
    return response
export_csv_preferences.short_description = u"Export CSV"


def export_csv_order(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=mymodel.csv'

    if not request.user.has_perm('customers.export_order'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)

    writer.writerow([
        smart_str(u"id"),
        smart_str(u"status"),
        smart_str(u"creation_date"),
        smart_str(u"shipping_date"),
        smart_str(u"customer"),
        smart_str(u"coffee"),
        smart_str(u"amount"),
        smart_str(u"brew"),
        smart_str(u"package"),
        smart_str(u"different"),
        smart_str(u"recurrent"),
        smart_str(u"interval"),
        smart_str(u"voucher"),
        smart_str(u"feedback"),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.status),
            smart_str(obj.date),
            smart_str(obj.shipping_date),
            smart_str(obj.customer),
            smart_str(obj.coffee),
            smart_str(obj.amount),
            smart_str(obj.brew),
            smart_str(obj.get_package_display()),
            smart_str(obj.different),
            smart_str(obj.recurrent),
            smart_str(obj.interval),
            smart_str(obj.voucher),
            smart_str(obj.get_feedback_display()),
        ])
    return response
export_csv_order.short_description = u"Export CSV"


def export_subscribers(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse
    import mailchimp
    from django.conf import settings
    from customers.models import Customer
    from get_started.models import GetStartedResponse

    mailchimp_key = settings.MAILCHIMP_API_KEY

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=subscribers.csv'

    if not request.user.has_perm('customers.export_customer'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    try:
        unsubscribes = []
        m = mailchimp.Mailchimp(mailchimp_key)
        campaigns = m.campaigns.list(filters={'status':'sent'}, start=0, limit=1000)

        for c in campaigns['data']:
            total = m.reports.unsubscribes(cid=c['id'])['total']
            limit = 100
            pages = total // limit + 1
            temp_list = []

            for i in range(pages):
                for u in m.reports.unsubscribes(cid=c['id'], opts={'start':i, 'limit':limit})['data']:
                    temp_list.append(u['member']['email'].lower())

            unsubscribes += temp_list

        unsubscribes_set = set(unsubscribes)

    except mailchimp.Error, e:
        print 'MailChimp error occurred: %s - %s' % (e.__class__, e)

    customers = Customer.objects.all()
    get_started = GetStartedResponse.objects.all()
    customers_set = set([x.user.email.lower() for x in customers])
    get_started_set = set([x.email.lower() for x in get_started])
    subscribes_set = customers_set.union(get_started_set) - unsubscribes_set

    writer.writerow([
        smart_str(u"email"),
        # smart_str(u"mailchimp"),
    ])
    for email in subscribes_set:
        writer.writerow([
            smart_str(email),
            # smart_str('1'),
        ])
    # for email in unsubscribes_set:
    #     writer.writerow([
    #         smart_str(email),
    #         smart_str('0'),
    #     ])

    return response

export_subscribers.short_description = u"Export subscribers"


def export_not_ordered(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse
    import mailchimp
    from django.conf import settings
    from customers.models import Customer, Order
    from get_started.models import GetStartedResponse

    mailchimp_key = settings.MAILCHIMP_API_KEY

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=not_ordered.csv'

    if not request.user.has_perm('customers.export_customer'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    try:
        unsubscribes = []
        m = mailchimp.Mailchimp(mailchimp_key)
        campaigns = m.campaigns.list(filters={'status':'sent'}, start=0, limit=1000)

        for c in campaigns['data']:
            total = m.reports.unsubscribes(cid=c['id'])['total']
            limit = 100
            pages = total // limit + 1
            temp_list = []

            for i in range(pages):
                for u in m.reports.unsubscribes(cid=c['id'], opts={'start':i, 'limit':limit})['data']:
                    temp_list.append(u['member']['email'].lower())

            unsubscribes += temp_list

        unsubscribes_set = set(unsubscribes)

    except mailchimp.Error, e:
        print 'MailChimp error occurred: %s - %s' % (e.__class__, e)

    customers = Customer.objects.all()
    customers_set = set([x.user.email.lower() for x in customers])
    get_started = GetStartedResponse.objects.all()
    get_started_set = set([x.email.lower() for x in get_started])
    ordered_customers_set = set([x.customer.user.email.lower() for x in Order.objects.all()])
    subscribes_set = customers_set.union(get_started_set) - ordered_customers_set - unsubscribes_set

    writer.writerow([
        smart_str(u"email"),
    ])
    for email in subscribes_set:
        writer.writerow([
            smart_str(email),
        ])

    return response

export_not_ordered.short_description = u"Export signed up but not ordered"


def export_unsubscribes(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse
    import mailchimp
    from django.conf import settings
    from customers.models import Customer, Order
    from get_started.models import GetStartedResponse

    mailchimp_key = settings.MAILCHIMP_API_KEY

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=unsubscribes.csv'

    if not request.user.has_perm('customers.export_customer'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    try:
        unsubscribes = []
        m = mailchimp.Mailchimp(mailchimp_key)
        campaigns = m.campaigns.list(filters={'status':'sent'}, start=0, limit=1000)

        for c in campaigns['data']:
            total = m.reports.unsubscribes(cid=c['id'])['total']
            limit = 100
            pages = total // limit + 1
            temp_list = []

            for i in range(pages):
                for u in m.reports.unsubscribes(cid=c['id'], opts={'start':i, 'limit':limit})['data']:
                    temp_list.append(u['member']['email'].lower())

            unsubscribes += temp_list

        unsubscribes_set = set(unsubscribes)
        logger.debug('unsubscribes_set length {}'.format(len(unsubscribes_set)))

    except mailchimp.Error, e:
        logger.debug('Exception in export_unsubscribes()\n{}'.format(e))
        unsubscribes_set = []

    writer.writerow([
        smart_str(u"email"),
    ])
    for email in unsubscribes_set:
        writer.writerow([
            smart_str(email),
        ])

    return response

export_unsubscribes.short_description = u"Export unsubscribes"


def export_csv_gearorders(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=gear_orders.csv'

    if not request.user.has_perm('customers.export_gearorder'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)

    writer.writerow([
        smart_str(u'id'),
        smart_str(u'status'),
        smart_str(u'creation_date'),
        smart_str(u'shipping_date'),
        smart_str(u'customer'),
        smart_str(u'gear'),
        smart_str(u'quantity'),
        smart_str(u'price'),
        smart_str(u'details'),
        smart_str(u'tracking_number'),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.status),
            smart_str(obj.date),
            smart_str(obj.shipping_date),
            smart_str(obj.customer),
            smart_str(obj.gear),
            smart_str(obj.details.get('Quantity', 1)),
            smart_str(obj.price),
            smart_str(obj.details),
            smart_str(obj.tracking_number),
        ])
    return response
export_csv_gearorders.short_description = u"Export CSV"

def export_reactivation_stages(modeladmin, request, queryset):
    import csv
    import json
    from django.utils.encoding import smart_str
    from django.http import HttpResponse
    from get_started.models import GetStartedResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=reactivation_stages.csv'

    if not request.user.has_perm('customers.export_customer'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)

    writer.writerow([
        smart_str(u'id'),
        smart_str(u'email'),
        smart_str(u'stage'),
    ])
    for customer in queryset:

        try:
            gs_response = GetStartedResponse.objects.filter(email=customer.user.email).latest("created")
        except:
            pass
        else:
            sent_emails = json.loads(gs_response.sent_emails)
            if sent_emails:
                writer.writerow([
                    smart_str(customer.id),
                    smart_str(customer.user.email),
                    smart_str(sent_emails[-1]),
                ])
    return response
export_reactivation_stages.short_description = u"Export re-activation stages"


def export_csv_coffee_reviews(modeladmin, request, queryset):
    import csv
    from django.utils.encoding import smart_str
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=coffee_reviews.csv'

    if not request.user.has_perm('customers.export_coffeereview'):
        return response

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    writer.writerow([
        smart_str(u"id"),
        smart_str(u"created_at"),
        smart_str(u"rating"),
        smart_str(u"comment"),
        smart_str(u"coffee"),
        smart_str(u"order"),
        smart_str(u"amount"),
        smart_str(u"customer"),
        smart_str(u"stripe_id"),
    ])
    for obj in queryset:
        writer.writerow([
            smart_str(obj.id),
            smart_str(obj.created_at),
            smart_str(obj.rating),
            smart_str(obj.comment),
            smart_str(obj.order.coffee),
            smart_str(obj.order),
            smart_str(obj.order.amount),
            smart_str(obj.order.customer),
            smart_str(obj.order.customer.stripe_id),
        ])
    return response
export_csv_customer.short_description = u"Export CSV"


def personify(modeladmin, request, queryset):
    for voucher in queryset:
        voucher.personal = True
        voucher.save()
personify.short_description = u"Personify vouchers"


def unpersonify(modeladmin, request, queryset):
    for voucher in queryset:
        voucher.personal = False
        voucher.save()
unpersonify.short_description = u"Unpersonify vouchers"
