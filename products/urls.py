from django.urls import path
from .views import (CreateProductView, DeleteProductView, GetAllProducts, ProductDetailView,
    UpdateProductView, CreateVariationView, UpdateVariationView, DeleteVariationView, LandingProducts)


urlpatterns = [
    path('create/', CreateProductView.as_view(), name='product-create'),
    path('detail/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('update/<slug:slug>/', UpdateProductView.as_view(), name='product-update'),
    path('', GetAllProducts.as_view(), name='all-products'),
    path('landing-page/', LandingProducts.as_view(), name='all-products'),
    path('delete/<slug:slug>/', DeleteProductView.as_view(), name='product-delete'),
    path('create/variations/', CreateVariationView.as_view(), name='product_variation-create'),
    path('update/variations/<uuid:uuid>/', UpdateVariationView.as_view(), name='product_variation-update'),
    path('delete/variations/<uuid:uuid>/', DeleteVariationView.as_view(), name='product_variation-delete'),
]


