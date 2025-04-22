from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderViewSet, OrderItemViewSet,
    OrderStatusHistoryViewSet, MarketTransactionViewSet
)

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet)
router.register(r'order-status-history', OrderStatusHistoryViewSet)
router.register(r'transactions', MarketTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 