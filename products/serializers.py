from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductImage,
    Review
)

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url']
        
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = "__all__"

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']

class RelatedProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'price', 'images']

class ProductDetailSerializer(serializers.Serializer):
    product = ProductSerializer()
    reviews = ProductReviewSerializer(many=True)
    related_products = RelatedProductSerializer(many=True)

