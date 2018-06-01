#from django.test import TestCase
#from customers.factories.customer import AddressFactory

# Create your tests here.
def test_profile_view(client):
    resp = client.get('/registration/')
    assert resp.status_code == 200


#def test_profile_get_addresses_forms(mocker, request_mock):
#    address = AddressFactory()