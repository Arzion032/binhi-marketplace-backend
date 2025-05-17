from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    product_vendor = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = [
            'cart', 'product', 'product_id', 
            'quantity', 'product_vendor'
        ]
        
    def get_product_vendor(self, obj):
        # Adjust depending on your model field name: `vendor` or `seller`
        return {
            "id": str(obj.product.vendor.id),
            "name": obj.product.vendor.name
        } if obj.product and obj.product.vendor else None
        
    
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
        


