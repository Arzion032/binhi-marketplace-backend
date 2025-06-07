from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, MarketTransaction
from products.serializers import ProductSerializer
from users.serializers import UserSerializer       

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(source='variation.product', read_only=True)  # Get the product from the variation
    variation = serializers.CharField(source='variation.name', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variation', 'quantity', 'unit_price', 'subtotal', 'created_at']

    def get_subtotal(self, obj):
        return obj.unit_price * obj.quantity

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'changed_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    buyer = UserSerializer(read_only=True)  # Or serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_identifier', 'buyer', 'status', 'total_price', 'shipping_address', 
            'payment_method', 'created_at', 'updated_at', 'items', 'status_history'
        ]

class MarketTransactionSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    order = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = MarketTransaction
        fields = [
            'id', 'order', 'buyer', 'seller', 'payment_method', 'total_amount',
            'status', 'created_at', 'ended_at'
        ]
