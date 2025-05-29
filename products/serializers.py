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

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'category', 'vendor', 'status',
            'is_available', 'created_at', 'updated_at',
            'images', 'variations', 'min_price'
        ]
        
class LandingProductSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug',
            'images', 'min_price'
        ]

    def get_images(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image:
            return ProductImageSerializer(main_image).data  # Use the updated ProductImageSerializer
        return None

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']


class ProductDetailSerializer(serializers.Serializer):
    product = ProductSerializer()
    reviews = ProductReviewSerializer(many=True)
    related_products = LandingProductSerializer(many=True)
