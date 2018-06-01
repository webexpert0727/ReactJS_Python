from django.contrib import admin

# Register your models here.
from .models import (
                     Point,
                     Item,
                     RedemItem,
                     RedemPointLog,
                     GrantPointLog,
                     SetPoint,
                     CoffeeTypePoints,
                     OrderPoints,
                     Helper
                    )


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'points', 'added')
    search_fields = (
        'user__customer__first_name',
        'user__customer__last_name',
        'user__customer__phone',
        'user__email',
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'points', 'in_stock')


@admin.register(RedemItem)
class RedemItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'item', 'points', 'status', 'shipping_date')


# @admin.register(RedemPointLog)
# class RedemPointLogAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'points', 'item', 'added')


# @admin.register(GrantPointLog)
# class GrantPointLogAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'points', 'added')


# @admin.register(SetPoint)
# class SetPointAdmin(admin.ModelAdmin):
#     list_display = ('id', 'status', 'points')


# @admin.register(CoffeeTypePoints)
# class CoffeeTypePointsAdmin(admin.ModelAdmin):
#     list_display = ('id', 'coffee_type', 'points')

@admin.register(OrderPoints)
class OrderPointsAdmin(admin.ModelAdmin):
    list_display = ('sub_regular', 'sub_special', 'one_regular', 'one_special',\
        'credits')
    verbose_name_plural = 'Qq'
    class Meta:
        model = OrderPoints


admin.site.register(Helper)
