# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def test_index_page(admin_client):
    resp = admin_client.get('/manager/')
    assert resp.status_code == 200


def test_login_as_admin(admin_user, admin_json_client):
    resp = admin_json_client.post(
        '/manager/api/login/',
        {'username': admin_user.email,
         'password': 'password',
         'rememberme': True})
    assert resp.status_code == 200
    assert resp.json() == {'success': True, 'role': 'admin'}


def test_login_as_packer(packer_user, admin_json_client):
    resp = admin_json_client.post(
        '/manager/api/login/',
        {'username': packer_user.email,
         'password': 'password',
         'rememberme': True})
    assert resp.status_code == 200
    assert resp.json() == {'success': True, 'role': 'packer'}


def test_login_as_unauthorized(json_client):
    resp = json_client.post(
        '/manager/api/login/',
        {'username': 'user',
         'password': 'password'})
    assert resp.status_code == 401
    assert resp.json() == {
        'success': False,
        'role': None,
        'errors': {'__all__': [
            'Please enter a correct Email address and password. '
            'Note that both fields may be case-sensitive.']}
    }
