from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from collections import defaultdict
from cart.models import Cart, CartItem
from products.models import ProductVariation
from orders.serializers import OrderSerializer
from .models import Order, OrderItem, OrderStatusHistory, MarketTransaction
from users.models import CustomUser  
from uuid import UUID
import json

class ConfirmCheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        data = request.data
        buyer = request.user

        variation_ids = data.get("variation_ids", [])
        shipping_address = data.get("shipping_address")
        payment_method = data.get("payment_method")
        delivery_method = data.get("delivery_method")

        if not variation_ids or not shipping_address or not payment_method:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        cart = Cart.objects.get(user=buyer)
        cart_items = CartItem.objects.select_related('variation__product__vendor').filter(
            cart=cart,
            variation_id__in=variation_ids
        )

        # Log incoming data for debugging
        print("Variation IDs:", variation_ids)
        cart_variation_ids = cart_items.values_list('variation_id', flat=True)
        print("Cart Items Variation IDs:", cart_variation_ids)
        
        # Convert only the variation_ids to UUID, if they are not already UUIDs
        variation_ids = [UUID(v) if not isinstance(v, UUID) else v for v in variation_ids]

        # Cart items' variation IDs are already UUIDs, no need to convert them again
        cart_variation_ids = cart_items.values_list('variation_id', flat=True)

        # Now compare both as UUIDs
        missing_variations = [v for v in variation_ids if v not in cart_variation_ids]
        print("Missing Variations:", missing_variations)

        if missing_variations:
            return Response({"error": f"Variation(s) {missing_variations} are not in the cart."}, status=status.HTTP_400_BAD_REQUEST)

        print("this loop1")
        # Group cart items by vendor
        vendor_items = defaultdict(list)
        for item in cart_items:
            vendor_items[item.variation.product.vendor].append(item)

        order_ids = []
        response_orders = []

        print("this loop2")
        # Each vendor gets their own order
        for vendor, items in vendor_items.items():
            order_total = 0
            # Calculate total for this vendor's order
            for item in items:
                if item.variation.stock < item.quantity:
                    return Response({"error": f"Not enough stock for {item.variation.name}."}, status=status.HTTP_400_BAD_REQUEST)
                order_total += item.quantity * item.variation.unit_price

            print("order")
            # Create the order
            order = Order.objects.create(
                buyer=buyer,
                status='pending',
                total_price=order_total,
                shipping_address=shipping_address,
                payment_method=payment_method,
                delivery_method=delivery_method
            )

            print("order stats")
            # Status history
            OrderStatusHistory.objects.create(
                order=order, 
                status='pending'
                )

            # Create OrderItems, update stock
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    variation=item.variation,
                    quantity=item.quantity,
                    unit_price=item.variation.unit_price
                )
                # Decrement product stock
                item.variation.stock -= item.quantity
                if item.variation.stock <= 0:
                    item.variation.status = 'out_of_stock'
                    item.variation.is_available = False
                item.variation.save()
                
            print("market trans")
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
        print("Cart items to be deleted:", cart_items)

        cart_items.delete()

        return Response({
            "message": "Orders created successfully.",
            "orders": response_orders
        }, status=status.HTTP_201_CREATED)
        
class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Retrieve orders for the authenticated user
        orders = Order.objects.filter(buyer=request.user).order_by('-created_at')

        # Serialize orders
        serializer = OrderSerializer(orders, many=True)

        # Transform data to match the required response format
        order_history = []
        for order in serializer.data:
            order_data = {
                'id': order['id'],
                'orderId': order['order_identifier'],
                'status': order['status'],
                'total_price': order['total_price'],
                'shipping_address': order['shipping_address'],
                'payment_method': order['payment_method'],
                'orderDate': order['created_at'],
                'items': [],
                'sellerName': '',
                'sellerProfile': '',
                'deliveryAddress': {
                    'name': order['shipping_address'],  # You can map this better if you split address into name, phone, etc.
                    'phone': '',  # Placeholder for phone number if available
                    'address': order['shipping_address'],
                },
            }

            # Populate items for this order
            for item in order['items']:
                item_data = {
                    'name': item['product']['name'],
                    'image': item['product']['images'][0] if item['product']['images'] else None,  # Assuming image is a list
                    'quantity': item['quantity'],
                    'price': item['unit_price'],
                    'variation': item['variation'],  # This should now be available in the serialized data
                }
                order_data['items'].append(item_data)

            # Get seller details
            if order['items']:
                seller_id = order['items'][0]['product']['vendor']  # This is the seller's UUID
                try:
                    seller = CustomUser.objects.get(id=seller_id)  # Fetch the actual CustomUser instance using the UUID
                    order_data['sellerName'] = seller.username  # Access the username
                    # Check if the seller has a profile and safely access it
                    if hasattr(seller, 'profile'):
                        order_data['sellerProfile'] = seller.profile.profile_picture
                    else:
                        order_data['sellerProfile'] = None
                except CustomUser.DoesNotExist:
                    order_data['sellerName'] = 'Unknown'
                    order_data['sellerProfile'] = None

            order_history.append(order_data)
                # Pretty-print the order_history JSON
        pretty_order_history = json.dumps(order_history, indent=4)

        # Print the pretty-printed order history for debugging
        print(pretty_order_history)
        return Response(order_history)
