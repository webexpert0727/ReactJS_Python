from django.shortcuts import render


def my_custom_page_not_found_view(request):
    response = render(request, '404.html')
    response.status_code = 404

    return response


def my_custom_error_view(request):
    response = render(request, '500.html')
    response.status_code = 500

    return response


def my_custom_permission_denied_view(request):
    response = render(request, '403.html')
    response.status_code = 403

    return response


def my_custom_bad_request_view(request):
    response = render(request, '400.html')
    response.status_code = 400

    return response
