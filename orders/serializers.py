from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, MarketTransaction
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_id', 
            'quantity', 'price', 'created_at', 'updated_at'
        ]

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'order', 'status', 'changed_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'buyer_name', 'status', 'total_price',
            'shipping_address', 'payment_method', 'items', 
            'status_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['buyer']

class MarketTransactionSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)

    class Meta:
        model = MarketTransaction
        fields = [
            'id', 'order', 'buyer', 'buyer_name', 'seller', 
            'seller_name', 'payment_method', 'total_amount', 
            'status', 'created_at', 'ended_at'
        ]
        read_only_fields = ['buyer', 'seller'] 