from django.contrib import admin
from .models import RoadbullOrder


@admin.register(RoadbullOrder)
class RoadbullOrderAdmin(admin.ModelAdmin):
    list_display = (
        'gear_order', 'created', 'order_number', 'tracking_number',)
    search_fields = ('order_number', 'tracking_number',)

    raw_id_fields = ('gear_order',)

    exclude = ('label_pdf',)

    readonly_fields = ('created',)
