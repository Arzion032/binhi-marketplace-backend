from rest_framework import serializers
from .models import (
    Category,
    Product,
    ProductImage,
    Review
)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product', 'buyer', 'buyer_username', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['buyer']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    vendor_username = serializers.CharField(source='vendor.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'category', 'category_name', 'vendor', 'vendor_username',
            'status', 'created_at', 'updated_at', 'is_available',
            'images', 'reviews', 'average_rating'
        ]
        read_only_fields = ['vendor']

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews) 