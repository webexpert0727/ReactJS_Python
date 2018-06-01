# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import random

from django_countries.fields import CountryField

from django_hstore import hstore, query

from adminsortable.models import SortableMixin

from django.db import models
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy as _p
from django.utils.translation import ugettext_lazy as _
from customauth.models import MyUser
from django.contrib.postgres.fields import ArrayField

BODY_CHOICES = (
    (1, _('Light Roast')),
    (2, _('Light-Medium Roast')),
    (3, _('Medium Roast')),
    (4, _('Medium-Dark Roast')),
    (5, _('Dark Roast')),
)

LABEL_POS = (
    (1, 'Left'),
    (2, 'Right'),
)

BREW_METHODS_ORDER = [
    'Espresso', 'Drip', 'Aeropress', 'French press',
    'Stove top', 'Cold Brew', 'Nespresso', 'None']


class BrewMethodManager(models.Manager):
    def sorted(self, *args, **kwargs):
        def _sort(brew_method):
            try:
                n = BREW_METHODS_ORDER.index(brew_method.name)
            except ValueError:
                # for methods which are already in the database,
                # but not yet added to BREW_METHODS_ORDER
                n = len(BREW_METHODS_ORDER) - 2
            return n
        return list(sorted(
            super(BrewMethodManager, self).get_queryset().filter(*args, **kwargs),
            key=_sort))


class CoffeeTypeQuerySet(query.HStoreQuerySet):

    def active(self):
        """Return only active coffees."""
        return self.filter(mode=True)

    def bags(self):
        """Return non nespresso, non bottled coffee."""
        return (self.non_tasters()  # EXCLUDE_COFFEES
                .exclude(brew_method__name_en='Nespresso')
                .exclude(id__in=self.bottled().values_list('id', flat=True)))

    def nespresso(self):
        """Return nespresso coffee."""
        return (self.non_tasters()  # EXCLUDE_COFFEES
                    .filter(brew_method__name_en='Nespresso'))

    def non_tasters(self):
        return self.exclude(Q(name__icontains='Taster') |
                            Q(discovery=True))

    def tasters(self):
        return self.filter(Q(name__icontains='Taster') |
                           Q(discovery=True))

    def bottled(self):
        """Return bottled coffee only."""
        return (self.non_tasters()
                .annotate(methods=Count('brew_method'))
                .filter(methods=1, brew_method__name_en='Cold Brew'))

    def avg_rating(self):
        """Return coffees with AVG rating."""
        return (self.filter(reviews__rating__isnull=False, reviews__hidden=False)
                    .annotate(avg_rating=Avg('reviews__rating')))

    def best_seller(self, *args, **kwargs):
        kwargs.setdefault('order__status', 'SH')
        return (self.active()
                    .filter(*args, **kwargs)
                    .annotate(num_orders=Count('order', distinct=True))
                    .order_by('-num_orders')
                    .first())


class CoffeeTypeManager(hstore.HStoreManager):
    def get_queryset(self):
        # for calling custom QuerySet methods from the manager
        return CoffeeTypeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def bags(self, only_active=True):
        qs = self.get_queryset()
        if only_active:
            qs = qs.active()
        return qs.bags()

    def nespresso(self, only_active=True):
        qs = self.get_queryset()
        if only_active:
            qs = qs.active()
        return qs.nespresso()

    def bottled(self, only_active=True):
        qs = self.get_queryset()
        if only_active:
            qs = qs.active()
        return qs.bottled()

    def non_tasters(self, only_active=True):
        qs = self.get_queryset()
        if only_active:
            qs = qs.active()
        return qs.non_tasters()

    def tasters(self, only_active=True):
        qs = self.get_queryset()
        if only_active:
            qs = qs.active()
        return qs.tasters()

    def avg_rating(self):
        return self.get_queryset().avg_rating()

    def best_seller(self, *args, **kwargs):
        return self.get_queryset().best_seller(*args, **kwargs)

    def first_discovery_pack(self):
        return (self.get_queryset().filter(
            name__in=['Shake Your Bun Bun!', 'Give me S\'mores', 'Guji Liya']))

    def discovery_pack(self, customer):
        from customers.models import CoffeeReview

        customer_packs = customer.orders.filter(coffee__discovery=True)
        is_first_pack = customer_packs.filter(status='SH').count() == 0
        if is_first_pack:
            return list(self.first_discovery_pack())

        available_coffees = self.bags().filter(special=False)
        didnt_like_coffee_ids = set(
            CoffeeReview.objects
            .filter(order__customer=customer, rating__lte=3)
            .values_list('coffee', flat=True))

        shipped_coffee_ids = set()
        for order in customer_packs:
            shipped_coffee_ids.update(order.get_discovery_coffee_ids())

        # sample without low rated coffees
        exclude_coffee_ids = list(didnt_like_coffee_ids)
        sample_coffees_1 = available_coffees.exclude(id__in=exclude_coffee_ids)

        # sample without low rated coffees and already shipped
        exclude_coffee_ids.extend(list(shipped_coffee_ids))
        sample_coffees_2 = available_coffees.exclude(id__in=exclude_coffee_ids)

        if len(sample_coffees_2) >= 3:
            sample_coffees = sample_coffees_2
        elif len(sample_coffees_1) >= 3:
            sample_coffees = sample_coffees_1
        else:
            sample_coffees = available_coffees
        res = random.sample(sample_coffees, 3)
        return res


class BrewMethod(models.Model):
    name = models.CharField(_('Brew method'), max_length=32)
    slug = models.SlugField(max_length=20, blank=True)
    img = models.ImageField()
    objects = BrewMethodManager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(BrewMethod, self).save(*args, **kwargs)


class Flavor(models.Model):
    name = models.CharField(_('Flavor'), max_length=32)
    img = models.ImageField()

    def __unicode__(self):
        return self.name


class CoffeeType(SortableMixin):
    name = models.CharField(_('Coffee name'), max_length=64)
    mode = models.BooleanField(_('Available'), default=True)
    unavailable = models.BooleanField(_('Temporary unavailable'), default=False)
    special = models.BooleanField(_('Special'), default=False)
    discovery = models.BooleanField(_('Discovery'), default=False)
    decaf = models.BooleanField(_('Decaffeinated'), default=False)
    blend = models.BooleanField(_('Blend'), default=False)
    maker = models.CharField(_('Coffee producer'), max_length=128)
    region = models.CharField(_('Region'), max_length=64)
    country = CountryField()
    taste = models.CharField(_('Coffee taste'), max_length=128)
    more_taste = models.CharField(_('More taste'), max_length=512)
    body = models.IntegerField(_('Roast'), choices=BODY_CHOICES)
    intensity = models.IntegerField(_('Intensity'), default=6)
    acidity = models.CharField(_('Acidity'), max_length=16, default='Medium')
    recommended_brew = models.ForeignKey(BrewMethod, related_name="coffees", blank=True, null=True)
    roasted_on = models.DateField(_('Roasted on'), blank=True, null=True, default=None)
    shipping_till = models.DateField(_('Shipping untill'), blank=True, null=True, default=None)
    amount = models.DecimalField(_('Amount'), max_digits=6, decimal_places=2, default=14)
    amount_one_off = models.DecimalField(_('Amount for One-off'), max_digits=6, decimal_places=2, default=18)

    profile = hstore.DictionaryField(default={})
    objects = CoffeeTypeManager()

    brew_method = models.ManyToManyField(BrewMethod)
    img = models.ImageField()
    img_moreinfo = models.ImageField(blank=True, null=True)
    label = models.FileField(upload_to='labels/', blank=True)
    label_drip = models.FileField(upload_to='labels/', blank=True)
    label_position = models.IntegerField(_('Position'), choices=LABEL_POS, default=1)
    description = models.CharField(_('Description'), max_length=2048, default=_('This coffee is good'))

    altitude = models.CharField(max_length=32, default='1256m')
    varietal = models.CharField(max_length=64, default=_('Arabica'))
    process = models.CharField(max_length=32, default=_p('coffee process', 'Natural'))

    weight = models.IntegerField('Shipping weight', default=200)

    the_order = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['the_order']

    def __unicode__(self):
        return '{} from {}, {}'.format(self.name, self.region, self.country.name)

    def __init__(self, *args, **kwargs):
        super(CoffeeType, self).__init__(*args, **kwargs)
        self.__important_fields = ['roasted_on', 'shipping_till', ]
        for field in self.__important_fields:
            setattr(self, '__original_%s' % field, getattr(self, field))

    def has_changed(self):
        for field in self.__important_fields:
            origin = '__original_%s' % field
            if getattr(self, field) != getattr(self, origin):
                return True
        return False

    def save(self, *args, **kwargs):
        if self.has_changed():
            for coffee in CoffeeType.objects.active() \
                    .exclude(name=self.name):
                coffee.roasted_on = self.roasted_on
                coffee.shipping_till = self.shipping_till
                super(CoffeeType, coffee).save()

        super(CoffeeType, self).save(*args, **kwargs)

    @cached_property
    def is_pods(self):
        if "Nespresso" in [x.name for x in self.brew_method.all()]:
            return True
        return False

    @cached_property
    def is_discovery_pack(self):
        return self.discovery is True

    @cached_property
    def hasLabel(self):
        return bool(self.label and self.label_drip)

    def is_bottled(self):
        return len(self.brew_method.all()) == 1 and self.brew_method.first().name_en == 'Cold Brew'

    def reviews_count(self):
        return self.reviews.filter(hidden=False).count()


class FarmPhotos(models.Model):
    coffee = models.ForeignKey(CoffeeType)
    photo1 = models.ImageField(blank=True)
    photo2 = models.ImageField(blank=True)
    photo3 = models.ImageField(blank=True)
    photo4 = models.ImageField(blank=True)
    photo5 = models.ImageField(blank=True)

    def __unicode__(me):
        return unicode(me.coffee)


class CoffeeGearColor(models.Model):
    name = models.CharField(_('Color name'), max_length=30)

    def __unicode__(self):
        return self.name


class CoffeeGear(SortableMixin):
    SET = 'set'
    CHRISTMAS = 'christmas'
    SPECIAL_CHOICES = (
        (SET, 'Set'),
        (CHRISTMAS, 'Christmas'),
    )
    name = models.CharField(_('Title'), max_length=64)
    essentials = models.BooleanField(_('Essentials'), default=True)
    model = models.CharField(_('Model'), max_length=32)
    description = models.CharField(_('Description'), max_length=512, blank=True)
    more_info = models.TextField(_('More info'), max_length=2048, blank=True)
    link = models.CharField(_('Watch brew guide link'), max_length=256, default="#")
    price = models.DecimalField(_('Price'), max_digits=6, decimal_places=2)
    in_stock = models.BooleanField(_('In Stock'), default=True)
    available = models.BooleanField(_('Available'), default=True)
    recommend = models.BooleanField(_('Recommend'), default=False)
    brew_methods = models.ManyToManyField(BrewMethod)
    special = models.CharField(
        'Special for', max_length=30, choices=SPECIAL_CHOICES, blank=True)
    allow_choice_package = models.BooleanField(
        'Allow the choice of packaging',
        default=False,
        help_text='Can a customer choose a package/brew method?')

    weight = models.IntegerField('Shipping weight', default=500)
    the_order = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['the_order']

    def __unicode__(self):
        return self.name

    def get_available_colors(self):
        av_colors = []
        for img in self.images.prefetch_related('color').all():
            if img.image and img.color:
                av_colors.append({
                    'color_id': img.color.id,
                    'color_name': img.color.name,
                    'img': img.image.url,
                })
        return json.dumps(av_colors)


class CoffeeGearImage(models.Model):
    coffee_gear = models.ForeignKey(CoffeeGear, related_name='images')
    image = models.ImageField()
    color = models.ForeignKey(
        CoffeeGearColor,
        related_name='+',
        blank=True,
        null=True,
    )

    def __unicode__(self):
        return '%s [%s]' % (self.image, self.color)


class CoffeeSticker(models.Model):
    coffee = models.ForeignKey(CoffeeType)
    name = models.CharField(_('Name'), max_length=256, blank=True, default='Hook Coffee Singapore')
    description = models.CharField(_('Description'), max_length=256, blank=True, default=(
        'We deliver specialty coffee, sourced from the world\'s best farms '
        'and hand-roasted locally in Singapore. Your fresh and delicious '
        'coffee is sent out to you within a week of roasting, just the way '
        'you want it, and straight to your mailbox! #IAMHOOKED'))
    caption = models.CharField(_('Caption'), max_length=256, blank=True, default='HOOKCOFFEE.COM.SG')
    hashtag = models.CharField(_('Hashtag'), max_length=256, blank=True, default='#HOOKCOFFEESG')
    sticker = models.FileField(upload_to='stickers/', default='stickers/sweet_bundchen_1024.png')

    def __unicode__(self):
        return '[%s] %s' % (self.hashtag, self.coffee)


class SharedCoffeeSticker(models.Model):
    customer = models.ForeignKey('customers.Customer', blank=True, null=True)
    user = models.BigIntegerField(_('User'), blank=False)
    post = models.BigIntegerField(_('Post'), blank=False)
    hashtag = models.CharField(_('Shared hashtag'), max_length=256, blank=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)

    def __unicode__(self):
        email = 'unknown' if not self.customer else self.customer.get_email()
        link = 'https://www.facebook.com/%s_%s' % (self.user, self.post)
        return '%s [%s] %s - %s' % (
            self.get_fmt_created_date(), email, self.hashtag, link)

    def get_fmt_created_date(self):
        return timezone.localtime(self.created).strftime('%b, %d (%H:%M)')


class RawBean(models.Model):
    name = models.CharField(_('Name'), max_length=256, unique=True)
    stock = models.DecimalField(_('Amount'), max_digits=6, decimal_places=2)
    status = models.BooleanField(_('Available'), default=True)
    created_date = models.DateTimeField(
        verbose_name='Created Date',
        auto_now_add=True
    )

    def __unicode__(self):
        return '%s: %skg' % (self.name, self.stock)


class CourseCategory(models.Model):
    name = models.CharField(_('Name'), max_length=256, unique=True)
    description = models.CharField(_('Description'), max_length=2048, default=_(''))

    def __unicode__(self):
        return '%s' % (self.name)


class WorkShops(models.Model):
    course_category = models.ForeignKey(CourseCategory)
    name = models.CharField(_('Name'), max_length=256, unique=True)
    description = models.CharField(_('Description'), max_length=2048, default=_('A good Course to know more about Coffee'))
    status = models.BooleanField(_('Available'), default=True)
    img = models.ImageField()
    slug = models.SlugField(max_length=20, blank=True)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    maker = models.CharField(_('Coffee producer'), max_length=128)
    country = CountryField()
    duration = models.IntegerField(_('Duration'), default=1)
    cost = models.DecimalField(_('Amount'), max_digits=6, decimal_places=2, default=14)

    def __unicode__(self):
        return '%s' % (self.name)


class WorkShopDates(models.Model):
    workshop = models.ForeignKey(WorkShops, related_name='workshopdates')
    date = models.DateTimeField()
    status = models.BooleanField(_('Open'), default=True)
    # TO DO: turn status to False when the dates reaches the maximum number of users.

    def __unicode__(self):
        return '%s-%s-%s' % (self.workshop.name, self.date, self.status)
