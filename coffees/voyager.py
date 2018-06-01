from django.shortcuts import render


def index(request):
    return render(request, 'coffees/voyager/index.html')


def drip_coffee_bags(request):
    return render(request, 'coffees/voyager/Drip coffee bags.html')


def perfectly_ground(request):
    return render(request, 'coffees/voyager/Perfectly ground.html')
