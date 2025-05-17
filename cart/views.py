from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from collections import defaultdict



class CartView(APIView):
    def get(self,request):
        
        cart_items = CartItem.objects.select_related('product__vendor').filter(cart__user=request.user)
        
        vendor_items = defaultdict()
        
        for item in cart_items:
            vendor = item.product.vendor
            vendor_items[vendor.id].append(item)
            
        response_data = []
        
        for vendor_id, items in vendor_items.items():
            vendor = items[0].product.vendor
            serializer = CartItemSerializer(items, many=True)
            response_data.append({
                'vendor_id': vendor,
                'vendor_name': vendor.name,
                'items': serializer.data
            })
            
        return Response(response_data)
    
    
class AddToCart(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Get or create cart for the user
        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Inject cart into validated data before saving
        data = request.data.copy()
        data['cart'] = cart.id

        serializer = CartItemSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class UpdateCartItem(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = request.data.get('quantity')

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
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)
