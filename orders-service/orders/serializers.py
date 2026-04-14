import requests
from django.conf import settings
from rest_framework import serializers
from .models import Order, OrderLine


def fetch_product(product_id):
    """Récupère un produit depuis le catalog-service."""
    catalog_url = getattr(settings, 'CATALOG_SERVICE_URL', 'http://localhost:8001')
    try:
        response = requests.get(f"{catalog_url}/api/products/{product_id}/", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise serializers.ValidationError(
            f"Impossible de récupérer le produit {product_id} depuis le catalog-service : {e}"
        )


class OrderLineSerializer(serializers.ModelSerializer):
    unit_price = serializers.CharField(read_only=True)
    line_total = serializers.CharField(read_only=True)

    class Meta:
        model = OrderLine
        fields = ['product_id', 'product_name', 'unit_price', 'quantity', 'line_total']
        read_only_fields = ['product_name']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être supérieure à 0.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderLineSerializer(many=True)
    total_amount = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer_id', 'status', 'total_amount', 'created_at', 'items']
        read_only_fields = ['id', 'status', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        total = 0

        for item in items_data:
            p_id = item['product_id']
            qty = item['quantity']

            product = fetch_product(p_id)
            price = float(product['price'])
            name = product['name']
            line_total = price * qty

            OrderLine.objects.create(
                order=order,
                product_id=p_id,
                product_name=name,
                unit_price=price,
                quantity=qty,
                line_total=line_total,
            )
            total += line_total

        order.total_amount = total
        order.save()
        return order