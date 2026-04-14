from rest_framework import serializers

from .models import Address, Customer


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "street", "postal_code", "city", "country", "is_default"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "first_name", "last_name", "email", "phone", "is_active"]
