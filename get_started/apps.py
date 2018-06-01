from django.apps import AppConfig


class GetStartedConfig(AppConfig):
    name = 'get_started'
    verbose_name = 'Get Started'

    def ready(self):
        import get_started.signals
