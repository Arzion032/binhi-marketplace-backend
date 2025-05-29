from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConfirmCheckoutView

urlpatterns = [
    path('confirm/', 
        ConfirmCheckoutView.as_view(), 
        name ="checkout_view")
] 




