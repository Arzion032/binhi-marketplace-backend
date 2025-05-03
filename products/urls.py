from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView,
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
    ProductDetailsView,
    SameCategoryProductsView,
    ProductReviewsView,
    ProductImageListCreateView,
    ProductImageRetrieveUpdateDestroyView,
    ReviewListCreateView,
    ReviewRetrieveUpdateDestroyView
)

urlpatterns = [
    # Category URLs
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<uuid:id>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-retrieve-update-destroy'),

    # Product URLs
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<uuid:id>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-retrieve-update-destroy'),
    path('products/<uuid:id>/details/', ProductDetailsView.as_view(), name='product-details'),
    path('products/<uuid:id>/same-category/', SameCategoryProductsView.as_view(), name='same-category-products'),
    path('products/<uuid:id>/reviews/', ProductReviewsView.as_view(), name='product-reviews'),

    # Product Image URLs
    path('product-images/', ProductImageListCreateView.as_view(), name='product-image-list-create'),
    path('product-images/<uuid:id>/', ProductImageRetrieveUpdateDestroyView.as_view(), name='product-image-retrieve-update-destroy'),

    # Review URLs
    path('reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<uuid:id>/', ReviewRetrieveUpdateDestroyView.as_view(), name='review-retrieve-update-destroy'),
] 