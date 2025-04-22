from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    Review
)

admin.site.register([
    Category,
    Product,
    ProductImage,
    Review
])
