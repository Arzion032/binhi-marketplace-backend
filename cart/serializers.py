from rest_framework import serializers
from .models import Cart, CartItem
from products.serializers import ProductSerializer, ProductImageSerializer
from products.models import ProductVariation


class CartVariationSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductVariation
        fields = ['id', 'name', 'unit_price', 'unit_measurement', 'stock', 'is_available', 'product', 'main_image']

    def get_product(self, obj):
    # Fetch all variations of the product
        variations = obj.product.variations.all().values('id', 'name')
        
        return {
            'id': str(obj.product.id),
            'name': obj.product.name,
            'slug': obj.product.slug,
            'variations': list(variations),  # List of dicts with id & name
        }

    def get_main_image(self, obj):
        main_img = obj.images.filter(is_main=True).first()
        if main_img:
            return main_img.image
        return None

class CartItemSerializer(serializers.ModelSerializer):
    variation = CartVariationSerializer(read_only=True)
    variation_id = serializers.UUIDField(write_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)
    warning_message = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['cart', 'variation', 'variation_id', 'quantity', 'total_price', 'warning_message']

    def get_total_price(self, obj):
        return obj.quantity * obj.variation.unit_price

    def get_warning_message(self, obj):
        if obj.quantity >= obj.variation.stock or obj.variation.stock < 5:
            return f"Only {obj.variation.stock} left in stock."
        return None
    
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
        


