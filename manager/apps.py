from django.apps import AppConfig


class ManagerConfig(AppConfig):
    name = 'manager'
    verbose_name = 'Manager'

    def ready(self):
        import manager.signals
