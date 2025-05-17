from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsFarmer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from django.shortcuts import get_object_or_404
from .models import Product, Category, ProductImage, Review
from .serializers import ProductDetailSerializer, ProductSerializer


class ProductDetailView(APIView):
    def get(self, request, slug):
        product = get_object_or_404(Product.objects.select_related('category'), slug=slug)

        # Get product reviews
        reviews = product.reviews.all()

        # Get related products (same category, excluding itself)
        related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

        data = {
            'product': product,
            'reviews': reviews,
            'related_products': related_products
        }
        
        serializer = ProductDetailSerializer(data)
        return Response(serializer.data)
    
    
class CreateProductView(APIView):
    permission_classes = [IsAuthenticated, IsFarmer]
    def post(self, request):
        product_data = request.data.copy()
        product_data['vendor'] = request.user.id
        product_data['status'] = 'hidden'
        
        images = request.FILES.getlist('images')

        serializer = ProductSerializer(data=product_data)
        if serializer.is_valid():
            product = serializer.save()

            # Save images (if any)
            for img in images:
                ProductImage.objects.create(product=product, image_url=img)

            response_data = ProductSerializer(product).data
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   


class UpdateProductView(APIView):
    def patch(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        product_data = request.data.copy()
        new_images = request.FILES.getlist('images')

        serializer = ProductSerializer(product, data=product_data, partial=True)
        if serializer.is_valid():
            product = serializer.save()

            # If new images are provided, delete old ones and add new
            if new_images:
                product.images.all().delete()  # Assumes related_name='images' in ProductImage model
                for img in new_images:
                    ProductImage.objects.create(product=product, image_url=img)

            return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteProductView(APIView):
    def delete(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response({'message': f'Product {product.name} deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    
class GetAllProducts(APIView):

    permission_classes = [IsAuthenticated, IsFarmer]
    VALID_STATUSES = {
        'published', 'out_of_stock', 'hidden', 'pending_approval', 'rejected'
    }

    def get(self, request):
        user_id = request.query_params.get('user_id')
        status = request.query_params.get('status')

      
        products = Product.objects.all()

        if user_id:
            products = products.filter(vendor__id=user_id)

       
        if status and status in self.VALID_STATUSES:
            products = products.filter(status=status)

        else:
            products = products.filter(status='published')


        print(status)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    