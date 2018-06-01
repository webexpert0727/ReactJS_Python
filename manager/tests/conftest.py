import pytest

from django.contrib.auth.models import Group, Permission

from .utils import JSONClient


@pytest.fixture()
def admin_user(db, admin_user):
    """A Django admin user with group and permissions."""
    group, _ = Group.objects.get_or_create(name='admin')
    admin_user.groups.add(group)
    group.permissions.add(
        Permission.objects.get(codename='can_view_pack'),
        Permission.objects.get(codename='can_view_customers'),
        Permission.objects.get(codename='can_view_inventory'),
        Permission.objects.get(codename='can_view_marketing'),
        Permission.objects.get(codename='can_view_analysis'))
    return admin_user


@pytest.fixture()
def packer_user(db, django_user_model):
    """A Django packer user."""
    UserModel = django_user_model
    try:
        user = UserModel.objects.get_by_natural_key('packer@example.com')
    except UserModel.DoesNotExist:
        user = UserModel._default_manager.create_user(
            'packer@example.com', 'password')
    group, _ = Group.objects.get_or_create(name='packer')
    user.groups.add(group)
    group.permissions.add(
        Permission.objects.get(codename='can_view_pack'),
        Permission.objects.get(codename='can_view_customers'),
        Permission.objects.get(codename='can_view_inventory'))
    return user


@pytest.fixture()
def admin_json_client(admin_user):
    """A Django test json client logged in as an admin user."""
    client = JSONClient()
    client.login(email=admin_user.email, password='password')
    return client


@pytest.fixture()
def json_client(admin_user):
    """A Django test json client."""
    return JSONClient()
