from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, ProductImageViewSet,
    ReviewViewSet, CartViewSet, OrderViewSet,
    OrderItemViewSet, OrderStatusHistoryViewSet,
    MarketTransactionViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet)
router.register(r'order-status-history', OrderStatusHistoryViewSet)
router.register(r'transactions', MarketTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 