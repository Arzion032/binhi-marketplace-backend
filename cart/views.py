from django.shortcuts import render
from rest_framework import viewsets, permissions, status
import rest_framework.decorators
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
import rest_framework.permissions
from django.shortcuts import get_object_or_404
from collections import defaultdict
from rest_framework.permissions import IsAuthenticated, AllowAny
from products.models import Product


class CartView(APIView):
    permission_classes = [IsAuthenticated]  # Add authentication requirement
    
    def get(self, request):
        cart_items = CartItem.objects.select_related('product__vendor').filter(cart__user=request.user)
        
        vendor_items = defaultdict(list)
        
        for item in cart_items:
            vendor = item.product.vendor
            vendor_items[vendor.id].append(item)
            
        response_data = []
        
        for vendor_id, items in vendor_items.items():
            vendor = items[0].product.vendor
            serializer = CartItemSerializer(items, many=True)
            response_data.append({
                'vendor_id': vendor.id,  
                'vendor_name': vendor.username,
                'items': serializer.data
            })
            
        return Response(response_data)
    
    
class AddToCart(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Get or create cart for the user
        cart, _ = Cart.objects.get_or_create(user=request.user)
        
        data = request.data
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        if not product_id:
            return Response({'error': 'product_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if item already exists in cart
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            # If it exists, update the quantity
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            # If it doesn't exist, create a new one
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )
        
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class UpdateCartItem(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        cart_item = get_object_or_404(CartItem, product_id=item_id, cart__user=request.user)
        quantity = int(request.data.get('quantity'))

        if quantity is None or int(quantity) < 1:
            return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()

        from .serializers import CartItemSerializer
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class RemoveCartItem(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, product_id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)


class OrderSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_ids = request.data.get('product_ids', [])
        if not product_ids:
            return Response({"error": "No product_ids provided."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.get(user=request.user)
        # Fetch only selected cart items
        cart_items = CartItem.objects.select_related('product__vendor').filter(
            cart=cart,
            product_id__in=product_ids
        )

        vendor_items = defaultdict(list)
        for item in cart_items:
            vendor_id = item.product.vendor.id
            vendor_items[vendor_id].append(item)

        response_data = []
        grand_total = 0
        all_warnings = []

        for vendor_id, items in vendor_items.items():
            vendor = items[0].product.vendor
            serializer = CartItemSerializer(items, many=True)
            sub_total = sum(item.quantity * item.product.unit_price for item in items)
            grand_total += sub_total

            for item_data in serializer.data:
                if item_data.get("warning_message"):
                    all_warnings.append({
                        "product_name": item_data.get("product", {}).get("name"),
                        "warning": item_data.get("warning_message"),
                    })

            response_data.append({
                'vendor_id': vendor.id,
                'vendor_name': getattr(vendor, 'username', str(vendor)),
                'items': serializer.data,
                'sub_total': sub_total
            })

        # If there are any warnings, return them as an error
        if all_warnings:
            return Response({
                "error": "Some cart items have issues with quantity vs. stock.",
                "warnings": all_warnings
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'vendors': response_data,
            'grand_total': grand_total
        })