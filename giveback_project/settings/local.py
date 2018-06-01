from .base import *  # noqa

INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE = (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
) + MIDDLEWARE

