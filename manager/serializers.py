# from rest_framework import serializers
# from coffees.models import CoffeeType, BrewMethod
# from customauth.models import MyUser
# from customers.models import Order, Customer
#
# class OrderSerializer(serializers.Serializer):
#     # id = serializers.IntegerField(read_only=True)
#     # customer = CustomerSerializer()
#     # coffee = CoffeeSerializer()
#     # brew_method = BrewMethodSerializer()
#     # packaging = serializers.CharField(max_length=100)
#     # date = serializers.DateTimeField()
#     # shipping_date = serializers.DateTimeField()
#     # status = serializers.CharField(max_length=100)
#     class Meta:
#         model = Order
#         fields = ('id', 'customer_set', 'coffee_set', 'brew_method_set', 'packaging', 'date', 'shipping_date', 'status')
#
# class CustomerSerializer(serializers.Serializer):
#     # id = serializers.IntegerField(read_only=True)
#     # myuser = MyUserSerializer()
#     # first_name = serializers.CharField(max_length=100)
#     # last_name = serializers.CharField(max_length=100)
#     class Meta:
#         model = Customer
#         fields = ('id', 'myuser_set', 'first_name', 'last_name')
#
# class MyUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MyUser
#         fields = ('email')
#
# class CoffeeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CoffeeType
#         fields = ('name', 'mode', 'special', 'maker', 'region', 'country', 'taste', 'more_taste', 'body', 'roasted_on', 'shipping_till', 'amount', 'profile', 'objects', 'brew_method_set', 'img', 'label', 'label_drip', 'label_position', 'description', 'altitude', 'varietal', 'process')
#
# class BrewMethodSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BrewMethod
#         fields = ('name', 'img')