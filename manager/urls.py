# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decorator_include import decorator_include

from django.conf.urls import url
from django.contrib.auth.decorators import permission_required

from manager import analysis_views
from manager import inventory_views
from manager import marketing_views
from manager import cluster_views

from . import customer_views
from .views import common, packing, dashboard


common_urls = [
    url(r'^api/login', common.ManagerLogin.as_view()),
    url(r'^api/logout', common.ManagerLogout.as_view()),
    url(r'^api/is_authenticated', common.IsAuthenticated.as_view()),
    url(r'^api/getAllCoffees/', common.get_all_coffee_types, name='get_all_coffee_types'),
    url(r'^api/getAvailableCoffees/', common.get_available_coffee_types,
        name='get_available_coffee_types'),
    url(r'^api/brewMethods$', common.BrewMethods.as_view(), name='get_all_brew_types'),
]

packer_urls = [
    url(r'^api/commands/processOrder/(?P<pk>\d+)$', packing.ProcessOrder.as_view()),
    url(r'^api/commands/switchCoffee$', packing.SwitchCoffee.as_view()),

    # FIXME: should be like:
    # url(r'^api/coffeeOrders?filter=declined$', packing.PackingOrders.as_view()),
    # url(r'^api/gearOrders$?', packing.PackingOrders.as_view()),
    # url(r'^api/redemOrders$', packing.PackingOrders.as_view()),
    url(r'^api/packingOrders$', packing.PackingOrders.as_view()),
    url(r'^api/bottledOrders$', packing.BottledOrders.as_view()),
    url(r'^api/declinedOrders$', packing.DeclinedOrders.as_view()),
    url(r'^api/unredeemedItems$', packing.UnredeemedItems.as_view()),
    url(r'^api/tasterPackOrders$', packing.TasterPackOrders.as_view()),
    url(r'^api/multipleOrders$', packing.MultipleOrders.as_view()),
    url(r'^api/gearOrders$', packing.GearOrders.as_view()),
    url(r'^api/christmasOrders$', packing.ChristmasOrders.as_view()),
    url(r'^api/worldWideCoffeeOrders$', packing.WorldWideCoffeeOrders.as_view()),
    url(r'^api/worldWideGearOrders$', packing.WorldWideGearOrders.as_view()),

    url(r'^api/coffeeModalItems/(?P<pk>\d+)$', packing.CoffeeModalItems.as_view()),
    url(r'^api/coffeesSampled/(?P<pk>\d+)$', packing.CoffeesSampled.as_view()),
    url(r'^api/customerHasMultipleOrders/(?P<pk>\d+)$', packing.CustomerHasMultipleOrders.as_view()),

    url(r'^api/orderCount/', common.orderCount, name='orderCount'),
    url(r'^api/orderLabels$', common.OrderLabels.as_view()),
    url(r'^api/orderAddresses$', common.OrderAddresses.as_view()),
    url(r'^api/orderPostcards$', common.OrderPostcards.as_view()),
    url(r'^api/customerAddress$', common.CustomerAddress.as_view()),
    url(r'^api/toBeShippedCount$', packing.ToBeShippedCount.as_view()),
]

customer_urls = [

    url(r'^api/getAllCustomers/', customer_views.get_all_customers, name='get_all_customers'),
    url(r'^api/customerOrders/', customer_views.customerOrders, name='customer_orders'),
    url(r'^api/getCustomerPreferences/', customer_views.getCustomerPreferences,
        name='get_customer_preferences'),
    url(r'^api/editCustomerPreferences/', customer_views.editCustomerPreferences,
        name='edit_customer_preferences'),
    url(r'^api/addOrder/', customer_views.addOrder, name='add_order'),
    url(r'^api/resendOrder/', customer_views.resendOrder, name='resend_order'),
    url(r'^api/getOrderDetails/', customer_views.getOrderDetails, name='get_order_details'),
    url(r'^api/editOrder/', customer_views.editOrder, name='edit_order'),
    url(r'^api/cancelOrder/', customer_views.cancelOrder, name='cancel_order'),
    url(r'^api/getOrderPrice/', customer_views.getOrderPrice, name='get_order_price'),
    url(r'^api/getFlavors/', customer_views.getFlavors, name='get_flavors'),
    url(r'^api/getVouchers/', customer_views.getVouchers, name='get_vouchers'),
]

analysis_urls = [
    url(r'^api/coffeePerformance$', dashboard.coffeePerformance),
    url(r'^api/voucherPerformance$', dashboard.voucherPerformance),
    url(r'^api/percentageCustomersByAge$', dashboard.percentageCustomersByAge),
    url(r'^api/usersFromGA$', dashboard.usersFromGA),
    url(r'^api/userChurnRate$', dashboard.userChurnRate),
    url(r'^api/newSignups$', dashboard.newSignups),
    url(r'^api/lifetimeValue', dashboard.lifetimeValue),
    url(r'^api/revenue$', dashboard.revenue),
    url(r'^api/activeCustomerBreakdown', dashboard.activeCustomerBreakdown),
    url(r'^api/activeCustomersByMonth$', dashboard.ActiveCustomersByMonth.as_view()),
    url(r'^api/decayCustomersByMonth$', dashboard.DecayCustomersByMonth.as_view()),

    url(r'^api/updateReportCard$', analysis_views.updateReportCard, name='update_report_card'),
    url(r'^api/getReportCard$', analysis_views.getReportCard, name='get_report_card'),
    url(r'^api/saveRecommendation$', analysis_views.saveRecommendation, name='save_recommendation'),
    url(r'^api/getRecommendation$', analysis_views.getRecommendation, name='get_recommendation'),
    url(r'^api/getCustomerSegments$', analysis_views.getCustomerSegments, name='get_customer_segments'),
    url(r'^api/executeKMeansClusteringForCustomerSegments$', cluster_views.executeKMeansClusteringForCustomerSegments,
        name='execute_kmeans_clustering_for_customer_segments'),
]

marketing_urls = [
    url(r'^api/getActiveCustomers', marketing_views.get_all_active_customers,
        name='get_active_customers'),
    url(r'^api/getInactiveCustomers', marketing_views.get_all_inactive_customers,
        name='get_inactive_customers'),
    url(r'^api/getMailchimpLists$', marketing_views.getMailchimpLists, name='get_email_lists'),
    url(r'^api/addEmailsToList', marketing_views.addEmailsToList, name='add_emails_to_list'),
    url(r'^api/getMailchimpCampaigns', marketing_views.getMailchimpCampaigns,
        name='get_email_campaigns'),
    url(r'^api/createMailchimpList', marketing_views.createMailchimpList,
        name='create_mailchimp_list'),
    url(r'^api/retrieveCampaignBreakdown', marketing_views.retrieveCampaignBreakdown,
        name='retrieve_campaign_breakdown'),
    url(r'^api/getCampaignReport$', marketing_views.getCampaignReport, name='get_campaign_report'),
    url(r'^api/getOpenedCampaignEmails$', marketing_views.getOpenedCampaignEmails, name='get_opened_campaign_emails'),
    url(r'^api/getClickedCampaignEmails$', marketing_views.getClickedCampaignEmails,
        name='get_clicked_campaign_emails'),
]

inventory_urls = [
    url(r'^api/getAllBeans$', inventory_views.getAllBeans, name='get_all_beans'),
    url(r'^api/addNewBean$', inventory_views.addNewBean, name='add_new_bean'),
    url(r'^api/updateBean$', inventory_views.updateBean, name='update_bean'),
    url(r'^api/getInactiveBeans$', inventory_views.getInactiveBeans, name='get_inactive_beans'),
    url(r'^api/getActiveBeans$', inventory_views.getActiveBeans, name='get_active_beans'),
    url(r'^api/updateThreshold$', inventory_views.updateThreshold, name='update_threshold'),
    url(r'^api/getThreshold$', inventory_views.getThreshold, name='get_threshold'),
]


patterned = common_urls + [
    url(r'^', decorator_include(permission_required('manager.can_view_pack', login_url='/manager'), packer_urls)),
    url(r'^', decorator_include(permission_required('manager.can_view_customers', login_url='/manager'), customer_urls)),
    url(r'^', decorator_include(permission_required('manager.can_view_inventory', login_url='/manager'), inventory_urls)),
    url(r'^', decorator_include(permission_required('manager.can_view_marketing', login_url='/manager'), marketing_urls)),
    url(r'^', decorator_include(permission_required('manager.can_view_analysis', login_url='/manager'), analysis_urls)),
    url(r'', common.Index.as_view())
]


urlpatterns = patterned
