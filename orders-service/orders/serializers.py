from rest_framework import serializers
from .models import Order, OrderLine

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

        mock_prices = {1: 129.90, 3: 39.90}
        mock_names = {1: "Nike Air Zoom", 3: "Puma Rider"}

        for item in items_data:
            p_id = item['product_id']
            price = mock_prices.get(p_id, 0.0)
            name = mock_names.get(p_id, "Unknown Product")

            qty = item['quantity']
            line_total = float(price) * qty

            OrderLine.objects.create(
                order=order,
                product_id=p_id,
                product_name=name,
                unit_price=price,
                quantity=qty,
                line_total=line_total
            )
            total += line_total

        order.total_amount = total
        order.save()
        return order