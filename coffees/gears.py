from django.shortcuts import render
from coffees.models import CoffeeGear


def essentials(request):
    gears = CoffeeGear.objects.filter(
        essentials=True,
        in_stock=True,
        available=True,
        special='',
    ).prefetch_related('images')

    return render(request, 'coffees/gears/essentials.html', {'gears': gears})


def machines(request):
    gears = CoffeeGear.objects.filter(
        essentials=False, # machines
        in_stock=True,
        available=True,
        special='',
    ).prefetch_related('images')

    return render(request, 'coffees/gears/machines.html', {'gears': gears})
