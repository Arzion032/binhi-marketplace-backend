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
from products.models import ProductVariation


class CartView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Select related variation and variation's product vendor for efficient queries
        cart_items = CartItem.objects.select_related('variation__product__vendor').filter(cart__user=request.user)
        
        vendor_items = defaultdict(list)
        
        for item in cart_items:
            vendor = item.variation.product.vendor
            vendor_items[vendor.id].append(item)
        
        response_data = []
        
        for vendor_id, items in vendor_items.items():
            vendor = items[0].variation.product.vendor
            serializer = CartItemSerializer(items, many=True)
            response_data.append({
                'vendor_id': vendor.id,
                'vendor_name': getattr(vendor, 'username', str(vendor)),
                'items': serializer.data
            })
        
        return Response(response_data)
    
    
class AddToCart(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        data = request.data
        variation_id = data.get('variation_id')
        quantity = int(data.get('quantity', 1))  # fallback to 1 if not provided

        if not variation_id:
            return Response({'error': 'variation_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            variation = ProductVariation.objects.get(id=variation_id)
        except ProductVariation.DoesNotExist:
            return Response({'error': 'Variation not found'}, status=status.HTTP_404_NOT_FOUND)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variation=variation,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class UpdateCartItem(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        # Get cart item based on cart_id (since item_id should be the cart item's ID, not variation_id)
        cart_item = get_object_or_404(CartItem, variation=item_id, cart__user=request.user)
        print('1')
        # Handle quantity update
        quantity = request.data.get('quantity')
        if quantity is not None:
            quantity = int(quantity)
            if quantity < 1:
                return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity
        print('2')
        # Handle variation update
        new_variation_id = request.data.get('variation_id')
        if new_variation_id is not None:
            try:
                new_variation = get_object_or_404(ProductVariation, id=new_variation_id)
                
                # Check if this variation already exists in the cart
                existing_item = CartItem.objects.filter(
                    cart=cart_item.cart, 
                    variation=new_variation
                ).exclude(id=cart_item.id).first()
                
                if existing_item:
                    # If variation already exists, merge quantities and delete current item
                    existing_item.quantity += cart_item.quantity
                    existing_item.save()
                    cart_item.delete()
                    cart_item = existing_item
                else:
                    # Update to new variation
                    cart_item.variation = new_variation
                    
            except ProductVariation.DoesNotExist:
                return Response({"error": "Invalid variation ID."}, status=status.HTTP_400_BAD_REQUEST)
        print('3')
        cart_item.save()

        # Serialize the cart item to return the updated data
        from .serializers import CartItemSerializer
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
class RemoveCartItem(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, item_id):
        # Get cart item based on variation_id (instead of product_id)
        cart_item = get_object_or_404(CartItem, variation_id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)

class OrderSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        variation_ids = request.data.get('variation_ids', [])
        if not variation_ids:
            return Response({"error": "No variation_ids provided."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.get(user=request.user)
        # Fetch only selected cart items (filtering by variation_id)
        cart_items = CartItem.objects.select_related('variation__product__vendor').filter(
            cart=cart,
            variation_id__in=variation_ids
        )

        vendor_items = defaultdict(list)
        for item in cart_items:
            vendor_id = item.variation.product.vendor.id
            vendor_items[vendor_id].append(item)

        response_data = []
        grand_total = 0
        all_warnings = []

        for vendor_id, items in vendor_items.items():
            vendor = items[0].variation.product.vendor
            serializer = CartItemSerializer(items, many=True)
            sub_total = sum(item.quantity * item.variation.unit_price for item in items)
            grand_total += sub_total

            # Collect warnings if quantity exceeds stock
            for item_data in serializer.data:
                if item_data.get("warning_message"):
                    all_warnings.append({
                        "product_name": item_data.get("variation", {}).get("name"),
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
