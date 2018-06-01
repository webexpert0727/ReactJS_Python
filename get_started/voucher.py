import logging
import ast

from jsonview.decorators import json_view
from giveback_project.helpers import geo_check
from django.views.decorators.http import require_POST

from customers.models import Voucher, Order, ShoppingCart
from get_started.models import GetStartedResponse, GiftVoucher, ReferralVoucher
from coffees.models import CoffeeType, CoffeeGear

logger = logging.getLogger("giveback_project." + __name__)


@json_view
@geo_check
@require_POST
def main(request, is_worldwide):
    """Apply voucher to an order during registration.

    Saves a voucher to session

    voucher-name -- voucher name
    """

    # where client came from
    from_get_started = request.session.get("from_get_started")
    from_shopping_cart = request.session.get("from_shopping_cart")
    session = request.session.items()
    voucher_name = request.POST.get("voucher-name").strip().upper()

    coffee_id = request.POST.get("coffee-id")
    is_discovery_pack = False
    is_special_coffee = False
    if coffee_id:
        try:
            coffee = CoffeeType.objects.get(id=coffee_id)
            is_discovery_pack = coffee.is_discovery_pack
            is_special_coffee = coffee.special
        except CoffeeType.DoesNotExist:
            coffee = None
    else:
        coffee = None

    # orders = request.POST.get("orders")
    # if orders:
    #     orders = ast.literal_eval(orders)
    #     if len(orders) == 1:
    #         try:
    #             coffee = CoffeeType.objects.get(name=orders[0][0])
    #             is_discovery_pack = coffee.is_discovery_pack
    #             is_special_coffee = coffee.special
    #         except CoffeeType.DoesNotExist:
    #             coffee = None

    result = {}

    amount = get_total_amount(from_get_started, from_shopping_cart, session, coffee_id)
    voucher = find_voucher(request, voucher_name)

    mutually_exclusive = ['Introductory', 'Re-engagement']
    if request.user.is_authenticated:
        customer = request.user.customer
        used_mutually_exclusive = (
            customer.vouchers
            .select_related('category')
            .filter(category__name__in=mutually_exclusive)
            .exists())
    else:
        used_mutually_exclusive = False

    if voucher:
        if voucher["type"] == "basic" and not is_worldwide and not from_shopping_cart\
            and not (voucher["object"].category.name == "Introductory" and request.user.is_authenticated)\
            and not (voucher["object"].category.name in mutually_exclusive and used_mutually_exclusive)\
            and not is_special_coffee:

            voucher = voucher["object"]
            request.session["voucher"] = voucher.name
            result["found"] = True
            result["voucher"] = voucher.name
            if voucher.discount2:
                result["disc"] = "$" + str(voucher.discount2)
            else:
                result["disc"] = str(voucher.discount) + "%"

            result["new_price"] = amount - amount * voucher.discount / 100 - voucher.discount2

            if voucher.name == "V60STARTER":
                result["v60starter_kit_gift_voucher"] = True
                request.session["default_pack"] = "GR"
                request.session["V60STARTER"] = True
            elif voucher.name == "80GSTARTER":
                result["x80g_bag_gift_voucher"] = True
                request.session["default_pack"] = "WB"
                request.session["80GSTARTER"] = True
            elif voucher.name == "DRIPSTARTER":
                result["x3_drip_coffee_bags_gift_voucher"] = True
                request.session["default_pack"] = "DR"
                request.session["DRIPSTARTER"] = True
            elif voucher.name == "SHOTPODSSTARTER":
                result["shotpods_box_gift_voucher"] = True
                request.session["default_pack"] = "WB"
                request.session["SHOTPODSSTARTER"] = True
            elif voucher.name == "AEROPRESS25":
                result["aeropress_25_off"] = True
                request.session["AEROPRESS25"] = True
            elif voucher.name == "HUAT18":
                result["huat18"] = True
                request.session["HUAT18"] = True

        elif voucher["type"] == "gift_voucher" and not is_worldwide and not from_shopping_cart:
            voucher = voucher["object"]
            result["found"] = True
            result["new_price"] = 0
            result["gift_voucher"] = True
            result["gift_sender"] = voucher.sender_fname
            result["credits"] = voucher.amount
            request.session["friend"] = voucher.sender_fname
            request.session["credits"] = voucher.amount
            voucher.used = True
            voucher.save()

        elif voucher["type"] == "referral_voucher" and not is_worldwide and not from_shopping_cart:
            voucher = voucher["object"]
            result["found"] = True
            result["new_price"] = amount - amount * voucher.discount_percent / 100 - voucher.discount_sgd
            result["referral_voucher"] = True
            result["referral_sender"] = voucher.sender.first_name
            request.session["referral_voucher"] = voucher.code

        elif voucher["type"] == "worldwide_voucher" and is_worldwide:
            voucher = voucher["object"]
            coffee_cost = request.session.get("coffee_cost")
            try:
                request.session["voucher"] = voucher.name
                result["worldwide_voucher"] = True
                result["found"] = True
                new_price = coffee_cost - coffee_cost * voucher.discount / 100 - voucher.discount2
                result["new_price"] = new_price
            except:
                request.session["voucher"] = None
                result["found"] = False

        elif voucher["type"] == "cart_voucher" and from_shopping_cart and not is_special_coffee:
            voucher = voucher["object"]
            coffee_cost = request.session.get("coffee_cost", 0)
            request.session["voucher"] = voucher.name
            result["cart_voucher"] = True
            result["found"] = True
            new_price = coffee_cost - coffee_cost * voucher.discount / 100 - voucher.discount2
            result["new_price"] = new_price

        elif voucher["type"] == "gift_set_voucher" and not is_worldwide and from_shopping_cart:
            voucher = voucher["object"]
            result["found"] = True
            result["new_price"] = amount - amount * voucher.discount / 100 - voucher.discount2
            result["voucher"] = voucher.name
            request.session["voucher"] = voucher.name

        elif voucher["type"] == "gift_set_voucher" and not from_shopping_cart:
            request.session["voucher"] = None
            result["found"] = False
            result["sets_only"] = True

        elif voucher["type"] in ["basic", "gift_voucher", "referral_voucher", "gift_set_voucher"] and is_worldwide:
            request.session["voucher"] = None
            result["found"] = False
            result["sg_only"] = True

        elif voucher["type"] in ["basic", "gift_voucher", "referral_voucher"] and from_shopping_cart:
            request.session["voucher"] = None
            result["found"] = False
            result["subs_only"] = True

        elif (voucher["type"] == "special edition" and is_special_coffee and not is_discovery_pack and not from_shopping_cart)\
        or (voucher["type"] == "discover pack" and is_discovery_pack and not from_shopping_cart):
            voucher = voucher["object"]
            request.session["voucher"] = voucher.name
            result["found"] = True
            result["voucher"] = voucher.name
            if voucher.discount2:
                result["disc"] = "$" + str(voucher.discount2)
            else:
                result["disc"] = str(voucher.discount) + "%"

            result["new_price"] = amount - amount * voucher.discount / 100 - voucher.discount2

        elif (voucher["type"] == "special edition" and not is_special_coffee)\
        or (voucher["type"] == "special edition" and is_discovery_pack):
            request.session["voucher"] = None
            result["found"] = False
            result["special_only"] = True

        elif (voucher["type"] == "discover pack" and not is_discovery_pack):
            request.session["voucher"] = None
            result["found"] = False
            result["discovery_only"] = True

        elif voucher["type"] in ["basic", "gift_voucher", "referral_voucher", "cart_voucher", ] and is_special_coffee:
            request.session["voucher"] = None
            result["found"] = False
            result["basic_only"] = True

        else:
            request.session["voucher"] = None
            result["found"] = False

    return result


def get_total_amount(from_get_started, from_shopping_cart, session, coffee_id):
    amount = None

    if coffee_id:
        try:
            coffee = CoffeeType.objects.get(id=coffee_id)
            amount = coffee.amount
        except CoffeeType.DoesNotExist:
            logger.error("No coffee found with id={}".format(coffee_id))

    elif from_get_started:
        coffee_id = None
        for i in session:
            if i[0] == "coffee":
                coffee_id = i[1]
        if coffee_id:
            try:
                coffee = CoffeeType.objects.get(id=coffee_id)
                amount = coffee.amount
            except CoffeeType.DoesNotExist:
                logger.error("No coffee exists with id =", coffee_id)
        else:
            logger.error("No coffee found in session, session:", session)

    elif from_shopping_cart:
        cart = []
        coffee_ids = []
        amount = 0
        for i in session:
            if i[0] == "shopping-cart":
                cart = i[1]
        for i in cart:
            if i.get("coffee"):
                coffee_ids.append((i.get("coffee").get("id"), i.get("quantity"), "coffee"))
            elif i.get("gear"):
                coffee_ids.append((i.get("gear").get("id"), i.get("quantity"), "gear"))
        for i in coffee_ids:
            if i[2] == "coffee":
                try:
                    amount += CoffeeType.objects.get(id=i[0]).amount_one_off * i[1]
                except CoffeeType.DoesNotExist:
                    logger.error("No coffee exists with id =", i[0])
            elif i[2] == "gear":
                try:
                    amount += CoffeeGear.objects.get(id=i[0]).price * i[1]
                except CoffeeGear.DoesNotExist:
                    logger.error("No gear exists with id =", i[0])

    # WARNING: potentially hardcoded coffee price
    amount = amount or 14.

    return amount


def find_voucher(request, voucher_name):
    """Find voucher and determ its type.

    Returns voucher itself and the type as a dict
    """

    voucher = {}

    # apply THREE20 and HOOK4 vouchers to subscriptions only
    if voucher_name in ["THREE20", "HOOK4"] and request.session.get("alacarte"):
        return voucher

    v_obj = Voucher.objects.filter(mode=True, name=voucher_name)
    if v_obj.exists():
        v_obj = v_obj.get()
        v_type = "basic"
        cat = v_obj.category.name
        if cat == "Worldwide":
            v_type = "worldwide_voucher"
        elif cat == "shopping cart":
            v_type = "cart_voucher"
        elif cat == "special edition coffee":
            v_type = "special edition"
        elif cat == "discover pack":
            v_type = "discover pack"
        elif cat == "GiftSets":
            v_type = "gift_set_voucher"
        voucher["object"] = v_obj
        voucher["type"] = v_type
        return voucher

    try:
        # Send-a-friend voucher with Hook's credits
        voucher["object"] = GiftVoucher.objects.get(code=voucher_name)
        voucher["type"] = "gift_voucher"
    except GiftVoucher.DoesNotExist:
        pass
    else:
        return voucher

    try:
        # Referral programme voucher
        voucher["object"] = ReferralVoucher.objects.get(code=voucher_name)
        voucher["type"] = "referral_voucher"
    except ReferralVoucher.DoesNotExist:
        pass
    else:
        return voucher

    return voucher
