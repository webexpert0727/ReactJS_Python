import csv
from django.utils.encoding import smart_str
from django.http import HttpResponse
from customauth.models import MyUser
import logging

from .models import ReminderSkipDelivery
from customers.models.EmailManagement import EmailManagement


logger = logging.getLogger('giveback_project.' + __name__)

STATUS_CHOICES = {
    'AC': 'Active',
    'SH': 'Shipped',
    'PA': 'Paused',
    'CA': 'Canceled',
    'ER': 'Failed',
    'DE': 'Declined'
}

def export_csv_ab_reminders(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=AB_report.csv'

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    writer.writerow([
        smart_str(u"Email"),
        smart_str(u"Template"),
        smart_str(u"Skipped?"),
        smart_str(u"Order"),
        smart_str(u"Latest order status"),
    ])

    for obj in ReminderSkipDelivery.objects.filter(completed=True):
        try:
            customer = MyUser.objects.get(email=obj.email).customer
            em = EmailManagement.objects.get(token=obj.token)
        except MyUser.DoesNotExist as e:
            logger.error('Failed to find a user for email {}\n{}'.format(obj.email, e))
        except EmailManagement.DoesNotExist as e:
            logger.error('Failed to find EmailManagement object for email {}\n{}'.format(obj.email, e))
        except Exception as e:
            logger.error('{}'.format(e))
        else:
            writer.writerow([
                smart_str(obj.email),
                smart_str(obj.template_name),
                smart_str("No" if em.active else "Yes"),
                smart_str(obj.order),
                smart_str(STATUS_CHOICES.get(customer.get_last_order_status())),
            ])

    return response

export_csv_ab_reminders.short_description = "Export A/B testing report"

def mark_completed(modeladmin, request, queryset):
    for reminder in queryset:
        logger.info("Mark reminder [{}] as completed (previously {})".\
            format(reminder.id, "completed" if reminder.completed else "not completed"))
        reminder.completed = True
        reminder.save()
mark_completed.short_description = "Mark as completed"
