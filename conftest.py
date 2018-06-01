import logging

import pytest

from django.utils.translation import activate

from coffees.factories import (
    create_initial_brew_methods, create_initial_coffees,
    create_initial_flavors, create_initial_gears)

from customers.factories import create_initial_vouchers

from loyale.factories import (
    create_initial_loyale_items, create_initial_order_points)


@pytest.fixture(autouse=True)
def set_default_language():
    activate('en')


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(autouse=True)
def charge_mock(mocker):
    return mocker.patch('stripe.Charge.create', return_value={'id': 'ch_0001'})


@pytest.fixture(autouse=True)
def add_event_mock(mocker):
    return mocker.patch('customers.tasks.add_event.delay')


@pytest.fixture(autouse=True)
def create_intercom_profile_mock(mocker):
    return mocker.patch('customers.tasks.create_intercom_profile.delay')


@pytest.fixture(autouse=True)
def update_intercom_profile_mock(mocker):
    return mocker.patch('customers.tasks.update_intercom_profile.delay')


@pytest.fixture(autouse=True)
def mailchimp_subscribe_mock(mocker):
    return mocker.patch('customers.tasks.mailchimp_subscribe.delay')


@pytest.fixture(autouse=True)
def mailchimp_segment_member_del_mock(mocker):
    return mocker.patch('customers.tasks.mailchimp_segment_member_del.delay')


@pytest.fixture(autouse=True)
def stripe_get_card_fingerprint_mock(mocker):
    return mocker.patch('customers.tasks.stripe_get_card_fingerprint.delay')


@pytest.fixture(autouse=True)
def metric_mock(mocker):
    return mocker.patch('metrics.tasks.send_metric.delay')


@pytest.fixture(autouse=True)
def disable_logging(mocker):
    logging.disable(logging.CRITICAL)


# @pytest.fixture(scope='session')
# def django_db_setup():
#     """Avoid creating/setting up the test database"""
#     pass


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # instead fixtures
        create_initial_flavors()
        create_initial_brew_methods()
        create_initial_coffees()
        create_initial_gears()
        create_initial_loyale_items()
        create_initial_order_points()
        create_initial_vouchers()


@pytest.fixture()
def admin_user(db, django_user_model):
    """A Django admin user.
    This uses an existing user with username(email) "admin@example.com",
    or creates a new one with password "password".

    # ORIGINAL:
    # https://github.com/pytest-dev/pytest-django/blob/master/pytest_django/fixtures.py
    """
    UserModel = django_user_model
    email, password = ('admin@example.com', 'password')
    try:
        user = UserModel.objects.get_by_natural_key(email)
    except UserModel.DoesNotExist:
        user = UserModel._default_manager.create_superuser(email, password)
    return user


@pytest.fixture()
def admin_client(admin_user):
    """A Django test client logged in as an admin user.

    # ORIGINAL:
    # https://github.com/pytest-dev/pytest-django/blob/master/pytest_django/fixtures.py
    """
    from django.test.client import Client

    client = Client()
    client.login(email=admin_user.email, password='password')
    return client
