# -*- coding: utf-8 -*-

from __future__ import absolute_import

from decorator_include import decorator_include

from solid_i18n.urls import solid_i18n_patterns

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import (
    password_reset, password_reset_complete,
    password_reset_confirm, password_reset_done)
from django.views.generic.base import RedirectView, TemplateView
from django.views.i18n import JavaScriptCatalog

from coffees import voyager
from coffees.views import workshops
from coffees.gears import essentials, machines

from content.views import (BrewGuideDetailView, BrewGuideListView, careers,
                           privacy)
from customauth.views import login_user

from customers.views import (
    AnsweredExpSurvey, ApplyVoucher, CancelOrder,
    ChangeCustomerPassword, ChangeOrderAddress, ChangeOrderCoffee,
    ChangeOrderShippingDate, ChangePrimaryAddress, CreateAddress,
    CreateOrder, CreateOrderCoffeeReview, CreateRedem,
    DeleteAddress, PauseOrResumeOrder, ProfileView,
    ReferralFriends, UpdateAddress, UpdateCustomerDetails,
    UpdateOrderPreferences, change_stripe, CreateGiftAddress)
from customers.email_management import EmailManagementView

from manager.mailing_list import processMailchimpParams

from wholesale.views import WholesaleView

from .dashboard import (dashboard, print_address, print_all_addresses,
                        print_all_labels, print_label, process_global_orders,
                        qr_social, qr_social_coffees, update_order_status)
from .models import MyRegistrationView
from .shopping_cart import (
    add_bags, add_bottled, add_gear, add_pods, load_cart, update_cart, add_course)
from .taster import set_stripe_trial, taster3x80g, taster5x, trial
from .views import choose_country, index, social_data


unwrapped_translated_patterns = [
    url(r'^$', index, name='index'),
    url(r'^workshops/', workshops, name="Workshops"),
    url(r'^social_data/$', social_data, name='social_data'),
    url(r'^qr-social/(?:@(?P<order_id>[GR]?\d+)/)?$', qr_social, name='qr_social'),
    url(r'^accounts/register/$', MyRegistrationView.as_view()),
    url(r'^accounts/login/$', login_user, name='login_user'),
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^accounts/profile/$', ProfileView.as_view(), name='profile'),
    url(r'^accounts/change_stripe/$', change_stripe, name='change_stripe'),
    url(r'^accounts/create_address/$', CreateAddress.as_view(), name='create_address'),
    url(r'^accounts/create_gift_address/$', CreateGiftAddress.as_view(), name='create_gift_address'),
    url(r'^accounts/update_address/$', UpdateAddress.as_view(), name='update_address'),
    url(r'^accounts/delete_address/$', DeleteAddress.as_view(), name='delete_address'),
    url(r'^accounts/change_primary_address/$', ChangePrimaryAddress.as_view(), name='change_primary_address'),
    url(r'^accounts/create_order/$', CreateOrder.as_view(), name='create_order'),
    url(r'^accounts/update_order/$', UpdateOrderPreferences.as_view(), name='update_order'),
    url(r'^accounts/change_order_coffee/$', ChangeOrderCoffee.as_view(), name='change_order_coffee'),
    url(r'^accounts/change_order_address/$', ChangeOrderAddress.as_view(), name='change_order_address'),
    url(r'^accounts/change_order_schedule/$', ChangeOrderShippingDate.as_view(), name='change_order_schedule'),
    url(r'^accounts/create_order_review/$', CreateOrderCoffeeReview.as_view(), name='create_order_review'),
    url(r'^accounts/update_customer_details/$', UpdateCustomerDetails.as_view(), name='update_customer_details'),
    url(r'^accounts/change_customer_password/$', ChangeCustomerPassword.as_view(), name='change_customer_password'),
    url(r'^accounts/pause_resume_order/$', PauseOrResumeOrder.as_view(), name='pause_resume_order'),
    url(r'^accounts/cancel_order/$', CancelOrder.as_view(), name='cancel_one_order'),  # FIXME: one? see manager urls
    url(r'^accounts/voucher/$', ApplyVoucher.as_view(), name='profile_voucher'),
    url(r'^accounts/create_redem/$', CreateRedem.as_view(), name='create_redem'),
    url(r'^reset/password_reset/$', password_reset, name='reset_password_reset1'),
    url(r'^reset/password_reset/done/$', password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', password_reset_complete, name='password_reset_complete'),
    url(r'^coffees/', include('coffees.urls')),
    url(r'^about/', include('about.urls')),
    url(r'^getstarted/', include('get_started.urls')),
    url(r'^trial/(?P<which>.+)/', trial, name='trial'),
    url(r'^taster3x80g/', taster3x80g, name='taster3x80g'),
    url(r'^taster5x/', taster5x, name='taster5x'),
    url(r'^set_stripe_trial/$', set_stripe_trial, name='set_stripe_trial'),
    url(r'^careers/', careers, name='careers'),
    url(r'^privacy/', privacy, name='privacy'),
    url(r'^wholesale/', WholesaleView.as_view(), name='wholesale'),
    url(r'^brew-guides/$', BrewGuideListView.as_view(), name='brew_guide_list'),
    url(r'^brew-guides/(?P<slug>[\w\-]+)/$', BrewGuideDetailView.as_view(), name='brew_guide_details'),
    url(r'^2016/1?$', TemplateView.as_view(template_name='content/promo_2016.html'), name='promo_2016'),
    url(r'^referral-friends/$', ReferralFriends.as_view(), name='referral_friends'),
    url(r'^answered-exp-survey/$', AnsweredExpSurvey.as_view(), name='answered_exp_survey'),
    url(r'^choose-country/$', choose_country, name='choose_country'),

    url(r'^management/(?P<token>.+)', EmailManagementView.as_view())
]


translated_patterns = solid_i18n_patterns(
    url(r'^', decorator_include(processMailchimpParams, unwrapped_translated_patterns)),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='jsi18n'),
)

unwrapped_urlpatterns = [
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/favicons/base_favicon.ico', permanent=True)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^blog/', include('blog.urls')),
    url(r'^dashboard/$', dashboard, name='dashboard'),
    url(r'^update-order-status/$', update_order_status, name='update_order_status'),
    url(r'^qr-social-coffees/$', qr_social_coffees, name='qr_social_coffees'),
    url(r'^print_label/', print_label, name='print_label'),
    url(r'^print_address/', print_address, name='print_address'),
    url(r'^print_all_labels/', print_all_labels, name='print_all_labels'),
    url(r'^print_all_addresses/', print_all_addresses, name='print_all_addresses'),
    url(r'^process_global_orders/', process_global_orders, name='process_global_orders'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^manager/', include('manager.urls')),

    url(r'^gears/essentials$', essentials, name='gears_essentials'),
    url(r'^gears/machines$', machines, name='gears_machines'),

    url(r'^voyager/$', voyager.index, name='voyager'),
    url(r'^voyager/drip-coffee-bags$', voyager.drip_coffee_bags, name='drip_coffee_bags'),
    url(r'^voyager/perfectly-ground$', voyager.perfectly_ground, name='perfectly_ground'),

    url(r'^ckeditor/', include('ckeditor_uploader.urls')),

    url(r'^load-cart/$', load_cart, name='load-cart'),
    url(r'^update-cart/$', update_cart, name='update-cart'),
    url(r'^add-cart/$', add_bags, name='add-cart'),
    url(r'^add-cart/course/$', add_course, name='add_course'),

    url(r'^add-pods/$', add_pods, name='add-pods'),
    url(r'^add-gear/$', add_gear, name='add-gear'),
    url(r'^add-bottled/$', add_bottled, name='add-bottled'),
]

urlpatterns = (
    translated_patterns +
    unwrapped_urlpatterns +
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)


handler404 = 'giveback_project.views_errors.my_custom_page_not_found_view'
handler500 = 'giveback_project.views_errors.my_custom_error_view'
handler403 = 'giveback_project.views_errors.my_custom_permission_denied_view'
handler400 = 'giveback_project.views_errors.my_custom_bad_request_view'


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
