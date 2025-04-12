from rest_framework import serializers
from .models import (
    Category, Product, ProductImage, Cart, Order,
    OrderItem, OrderStatusHistory, MarketTransaction, Review
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'uploaded_at']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'vendor', 'category', 'stock',
            'price', 'slug', 'status', 'description',
            'created_at', 'updated_at', 'images'
        ]

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'product', 'quantity', 'added_at']
        read_only_fields = ['user']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'quantity', 'price', 'subtotal']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'order', 'status', 'changed_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'status', 'total_price',
            'created_at', 'items', 'status_history'
        ]
        read_only_fields = ['buyer']

class MarketTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketTransaction
        fields = [
            'id', 'order', 'buyer', 'seller', 'payment_method',
            'total_amount', 'status', 'created_at', 'ended_at'
        ]
        read_only_fields = ['buyer', 'seller']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'buyer', 'product', 'rating', 'comment', 'created_at']
        read_only_fields = ['buyer'] 