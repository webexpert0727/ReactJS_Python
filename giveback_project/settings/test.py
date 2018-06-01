from .base import *  # noqa


DEBUG = False
ALLOWED_HOSTS = ['*']

SECRET_KEY = 'CHANGEME'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# Keep templates in memory so tests run faster
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['debug'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

CELERY_ALWAYS_EAGER = True
