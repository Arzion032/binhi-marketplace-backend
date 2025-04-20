from rest_framework import serializers
from .models import (
    Category, Product, ProductImage, Review,
    Cart, CartItem, Order, OrderItem,
    OrderStatusHistory, MarketTransaction
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'uploaded_at']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 
            'stock', 'category', 'category_id', 
            'created_at', 'updated_at', 'is_available', 
            'vendor_name', 'status', 'images'
        ]

class ReviewSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'buyer', 'buyer_name', 'product', 
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['buyer']

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'cart', 'product', 'product_id', 
            'quantity', 'created_at', 'updated_at'
        ]

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'user_name', 'items', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user']

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