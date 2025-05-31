from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductImage,
    ProductVariation,
    VariationImage,
    Review
)

class ProductImageSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source='product.id', read_only=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'product_id', 'is_main']
        
class VariationImageSerializer(serializers.ModelSerializer):
    variation_id = serializers.UUIDField(source='variation.id', read_only=True)
    class Meta:
        model = VariationImage
        fields = ['id', 'image', 'variation_id', 'is_main']

class ProductVariationSerializer(serializers.ModelSerializer):
    images = VariationImageSerializer(many=True, read_only=True)
    class Meta:
        model = ProductVariation
        fields = ['id', 'product', 'name', 'unit_price', 'stock', 'is_available', 'images']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variations = ProductVariationSerializer(many=True, read_only=True)
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    vendor_name = serializers.SerializerMethodField()
    vendor_address = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'category', 'category_name','vendor', 'vendor_name', 'vendor_address', 'status',
            'is_available', 'created_at', 'updated_at',
            'images', 'variations', 'min_price'
        ]

    def get_vendor_name(self, obj):
        return obj.vendor.username if obj.vendor else None
    
    def get_category_name(self, obj):
        return obj.category.name if obj.vendor else None
    
    def get_vendor_address(self, obj):
        # Get the first address for the vendor (user)
        address = obj.vendor.addresses.first()
        if address:
            return {
                "city": address.city,
                "barangay": address.barangay,
                "street_address": address.street_address,
            }
        return None
        
        
class LandingProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    category_name = serializers.ReadOnlyField(source='category.name')  # This line adds the category name

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug',
            'images', 'min_price', 'category', 'category_name'
        ]

    def get_images(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return ProductImageSerializer(main_image).data
        return None

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']


class ProductDetailSerializer(serializers.Serializer):
    product = ProductSerializer()
    reviews = ProductReviewSerializer(many=True)
    related_products = LandingProductSerializer(many=True)
