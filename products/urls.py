from django.urls import path
from .views import (CreateProductView, DeleteProductView, GetAllProducts, ProductDetailView,
    UpdateProductView)


urlpatterns = [
    path('create/', CreateProductView.as_view(), name='product-create'),
    path('detail/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('update/<slug:slug>/', UpdateProductView.as_view(), name='product-update'),
    path('', GetAllProducts.as_view(), name='all-prodcts'),
    path('delete/<slug:slug>/', DeleteProductView.as_view(), name='product-delete'),

]


