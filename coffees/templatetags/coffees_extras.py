from django import template
from coffees.models import FarmPhotos, WorkShops, WorkShopDates


register = template.Library()


@register.simple_tag
def multiply(value, arg):
    return int(value) * int(arg)


@register.assignment_tag
def farm(coffee):
    photos = []
    try:
        farm = FarmPhotos.objects.get(coffee=coffee)

        if farm.photo1:
            photos.append(farm.photo1.url)
        if farm.photo2:
            photos.append(farm.photo2.url)
        if farm.photo3:
            photos.append(farm.photo3.url)
        if farm.photo4:
            photos.append(farm.photo4.url)
        if farm.photo5:
            photos.append(farm.photo5.url)
    except:
        pass

    return photos


@register.filter
def classname(obj):
    return obj.__class__.__name__


@register.simple_tag
def listing(collection):
    collection = list(collection)
    result = ""
    if collection:
        if len(collection) > 1:
            result = "| Loves {} and {}".format(", ".join([x.name for x in collection[:-1]]), collection[-1])
        else:
            el = collection[0].name
            if el != 'None':
                result = "| Loves {}".format(el)

    return result

@register.filter
def available_dates(workshop_id):
    """
    This function will returns the available dates for the
    workshop

    params: workshop id
    return: list of WorkShopDates objects
    """
    try:
        workshop = WorkShops.objects.get(id=workshop_id)
    except WorkShops.DoesNotExist:
        print "WorkShop DoesNotExist"
        return []
    else:
        return WorkShopDates.objects.filter(workshop=workshop, status=True)