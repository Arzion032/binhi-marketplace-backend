from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from collections import defaultdict
from cart.models import Cart, CartItem
from products.models import Product
from .models import Order, OrderItem, OrderStatusHistory, MarketTransaction
from users.models import CustomUser  

class ConfirmCheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        data = request.data
        buyer = request.user

        product_ids = data.get("product_ids", [])
        shipping_address = data.get("shipping_address")
        payment_method = data.get("payment_method")

        if not product_ids or not shipping_address or not payment_method:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.get(user=buyer)
        cart_items = CartItem.objects.select_related('product__vendor').filter(
            cart=cart,
            product_id__in=product_ids
        )

        if cart_items.count() != len(product_ids):
            return Response({"error": "One or more products are not in the cart."}, status=status.HTTP_400_BAD_REQUEST)

        # Group cart items by vendor
        vendor_items = defaultdict(list)
        for item in cart_items:
            vendor_items[item.product.vendor].append(item)

        order_ids = []
        response_orders = []

        # Each vendor gets their own order
        for vendor, items in vendor_items.items():
            order_total = 0
            # Calculate total for this vendor's order
            for item in items:
                if item.product.stock < item.quantity:
                    return Response({"error": f"Not enough stock for {item.product.name}."}, status=status.HTTP_400_BAD_REQUEST)
                order_total += item.quantity * item.product.unit_price

            # Create the order
            order = Order.objects.create(
                buyer=buyer,
                total_price=order_total,
                shipping_address=shipping_address,
                payment_method=payment_method
            )

            # Status history
            OrderStatusHistory.objects.create(order=order, status='pending')

            # Create OrderItems, update stock
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.unit_price
                )
                # Decrement product stock
                item.product.stock -= item.quantity
                if item.product.stock <= 0:
                    item.product.status = 'out_of_stock'
                    item.product.is_available = False
                item.product.save()

            # Create transaction (per vendor)
            MarketTransaction.objects.create(
                order=order,
                buyer=buyer,
                seller=vendor,
                payment_method=payment_method,
                total_amount=order_total,
                status='pending'
            )

            # Prepare response
            response_orders.append({
                "order_id": order.id,
                "vendor": vendor.username,
                "order_total": order_total
            })

            order_ids.append(order.id)

        # Remove these items from cart
        cart_items.delete()

        return Response({
            "message": "Orders created successfully.",
            "orders": response_orders
        }, status=status.HTTP_201_CREATED)
        