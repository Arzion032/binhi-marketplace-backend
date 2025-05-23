from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer, ProductImageSerializer
from products.models import Product


class CartProductSerializer(serializers.ModelSerializer):
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['slug', 'name', 'unit_price', 'vendor', 'main_image']

    def get_main_image(self, obj):
        main_images = obj.images.filter(is_main=True)
        return ProductImageSerializer(main_images, many=True).data

class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'cart', 'product', 'product_id', 
            'quantity', 'total_price']
    
    def get_total_price(self, obj):
        total_price = obj.quantity * obj.product.unit_price
        return total_price
    
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
        


