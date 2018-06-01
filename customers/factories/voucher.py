
import factory

from ..models import Voucher, VoucherCategory


class VoucherCategoryFactory(factory.django.DjangoModelFactory):
    name = 'Introductory'

    class Meta:
        model = VoucherCategory
        django_get_or_create = ('name',)


class VoucherFactory(factory.django.DjangoModelFactory):
    name = 'TRYUS50'
    mode = True
    discount = 0
    discount2 = 0
    count = 0
    category = factory.SubFactory(VoucherCategoryFactory)

    class Meta:
        model = Voucher
        django_get_or_create = ('name',)


def create_initial_vouchers():
    if Voucher.objects.all().count() > 0:
        return
    VoucherFactory(
        name='TRYUS50',
        category=VoucherCategoryFactory(name='Introductory'),
        discount=50)
    VoucherFactory(
        name='FB50',
        category=VoucherCategoryFactory(name='Introductory'),
        discount=50,
        mode=False)
    VoucherFactory(
        name='SHOTPODS50',
        category=VoucherCategoryFactory(name='Special'),
        discount=50)
    VoucherFactory(
        name='HIGH5',
        category=VoucherCategoryFactory(name='Introductory'),
        discount2=9)
    VoucherFactory(
        name='COFFEESCRUB',
        category=VoucherCategoryFactory(name='Special'))
    VoucherFactory(
        name='GLOBAL',
        category=VoucherCategoryFactory(name='Worldwide'),
        discount2=3)
    VoucherFactory(
        name='REFRESH50',
        category=VoucherCategoryFactory(name='Re-engagement'),
        discount=50)
    VoucherFactory(
        name='RESTOCK5',
        category=VoucherCategoryFactory(name='Re-engagement'),
        discount2=5)
    VoucherFactory(
        name='THREE20',
        category=VoucherCategoryFactory(name='REUSABLE'),
        discount=20)
    VoucherFactory(
        name='HOOK4',
        category=VoucherCategoryFactory(name='REUSABLE'),
        discount2=4)
