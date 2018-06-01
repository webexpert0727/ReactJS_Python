from django.apps import AppConfig
 
 
class CustomersConfig(AppConfig):
    name = 'customers'
    verbose_name = 'Stripe Integration'
 
    def ready(self):
        import customers.signals