from django.shortcuts import render
from rest_framework import viewsets, permissions
from django.db import models
from .models import Order, OrderItem, OrderStatusHistory, MarketTransaction
from .serializers import (
    OrderSerializer, OrderItemSerializer,
    OrderStatusHistorySerializer, MarketTransactionSerializer
)

# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(buyer_id=self.request.user.id)

class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__buyer_id=self.request.user.id)

class OrderStatusHistoryViewSet(viewsets.ModelViewSet):
    queryset = OrderStatusHistory.objects.all()
    serializer_class = OrderStatusHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderStatusHistory.objects.filter(order__buyer_id=self.request.user.id)

class MarketTransactionViewSet(viewsets.ModelViewSet):
    queryset = MarketTransaction.objects.all()
    serializer_class = MarketTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.user.id
        return MarketTransaction.objects.filter(
            models.Q(buyer_id=user_id) | models.Q(seller_id=user_id)
        )
