from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartView, AddToCart, UpdateCartItem, RemoveCartItem, OrderSummaryView


urlpatterns = [
     path('my_cart/', 
         CartView.as_view(), 
         name='my_cart'),
     path('add_to_cart/', 
         AddToCart.as_view(), 
         name='add_to_cart'),
     path('remove_cartitem/<uuid:item_id>/', 
         RemoveCartItem.as_view(), 
         name='delete_cartitem'),
     path('update_cartitem/<uuid:item_id>/', 
         UpdateCartItem.as_view(), 
         name='update-cart-item'),
     path('order_summary/', 
         OrderSummaryView.as_view(), 
         name='order_summary'),
     
] 