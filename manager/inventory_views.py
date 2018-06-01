import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse
from django.views.decorators.http import require_GET, require_POST

from manager import inventory_api
from manager.authentication import adminOnly



@require_GET
def getAllBeans(request):
    try:
        RESULT_JSON = {
            "status": 200,
            "beans": inventory_api.getAllBeans()
        }
    except Exception as e:
        RESULT_JSON = {
            "status": 500,
            "error_message": str(e)
        }
    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_POST
def addNewBean(request):
    data = json.loads(request.body)

    name = data['name']
    stock = data['stock']

    RESULT_JSON = inventory_api.processAddNewBean(name, stock)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')


@require_POST
def updateBean(request):
    data = json.loads(request.body)

    RESULT_JSON = inventory_api.processUpdateBean(data)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_GET
def getInactiveBeans(request):

    RESULT_JSON = inventory_api.processGetInactiveBeans()

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_GET
def getActiveBeans(request):

    dates = request.GET['dates']

    RESULT_JSON = inventory_api.processGetActiveBeans(dates)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_POST
def updateThreshold(request):
    data = json.loads(request.body)

    threshold = float(data['threshold'])

    RESULT_JSON = inventory_api.processUpdateThreshold(threshold)

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')



@require_GET
def getThreshold(request):

    RESULT_JSON = inventory_api.processGetThreshold()

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')