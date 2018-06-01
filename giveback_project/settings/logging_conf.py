import os

from .base import BASE_DIR

LOG_ROOT = os.getenv(
    'LOG_ROOT',
    default=os.path.join(os.path.dirname(BASE_DIR), 'logs'))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S:%MS'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt': '%d/%b/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_ROOT, 'debug.log'),
            'formatter': 'verbose',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
        },
        'file_order_processing': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_ROOT, 'order_processing.log'),
            'formatter': 'simple',
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'loggers': {
        'django': {
            'level': 'WARNING',
            'handlers': ['file'],
            'propagate': True,
        },
        'giveback_project': {
            'level': 'DEBUG',
            'handlers': ['file'],
        },
        'order_processing': {
            'level': 'DEBUG',
            'handlers': ['file_order_processing'],
        },
        'celery': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
        'raven': {
            'level': 'WARNING',
            'handlers': ['sentry'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'WARNING',
            'handlers': ['sentry'],
            'propagate': False,
        },
    }
}
