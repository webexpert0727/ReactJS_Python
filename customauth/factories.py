import factory

from django.contrib.auth.signals import user_logged_in, user_logged_out

from .models import MyUser


@factory.django.mute_signals(user_logged_in, user_logged_out)
class UserFactory(factory.Factory):
    email = factory.Faker('email')
    password = 'password'  # factory.PostGenerationMethodCall('set_password', 'password')

    class Meta:
        model = MyUser

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        return model_class.objects.create_user(*args, **kwargs)
