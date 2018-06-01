from django.http import HttpResponse
import json
from manager.cluster_api import processExecuteKMeansClusteringForCustomerSegments


def executeKMeansClusteringForCustomerSegments(request):
    RESULT_JSON = processExecuteKMeansClusteringForCustomerSegments()

    return HttpResponse(json.dumps(RESULT_JSON), content_type='application/json')