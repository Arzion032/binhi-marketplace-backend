from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import uuid

def generate_unique_slug(instance, field_value, slug_field_name='slug'):
    """
    Generate a unique slug for a model instance.
    """
    base_slug = slugify(field_value)
    slug = base_slug
    ModelClass = instance.__class__
    n = 1

    # Check for duplicates
    while ModelClass.objects.filter(**{slug_field_name: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base_slug}-{n}"
        n += 1

    return slug

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True,null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        
    def name_has_changed(self):
        if not self.pk:
            return True
        original = Category.objects.filter(pk=self.pk).first()
        return original and original.name != self.name
        
    def save(self, *args, **kwargs):
        if not self.slug or self.name_has_changed():
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('out_of_stock', 'Out of Stock'),
        ('hidden', 'Hidden'),
        ('pending_approval', 'Pending Approval'),
        ('deleted', 'Deleted'),
        ('rejected', 'Rejected')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', blank=True, null=True)
    vendor = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'farmer'},
        related_name='products'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def name_has_changed(self):
        if not self.pk:
            return True
        original = Product.objects.filter(pk=self.pk).first()
        return original and original.name != self.name

    def save(self, *args, **kwargs):
        if not self.slug or self.name_has_changed():
            self.slug = generate_unique_slug(self, self.name)
        super().save(*args, **kwargs)

    @property
    def min_price(self):
        return self.variations.filter(is_available=True).order_by('unit_price').first().unit_price if self.variations.exists() else None
    
    @property
    def unit_measurement(self):
        return self.variations.filter(is_available=True).first().unit_measurement if self.variations.exists() else None


class ProductVariation(models.Model):
    STATUS_CHOICES = (
        ('published', 'Published'),
        ('out_of_stock', 'Out of Stock'),
        ('hidden', 'Hidden'),
        ('pending_approval', 'Pending Approval'),
        ('deleted', 'Deleted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    name = models.CharField(max_length=100)  # e.g., "500g", "1kg", "Organic"
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    unit_measurement = models.CharField(max_length=100, default='per kg')
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_default = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')  # Added status field

    class Meta:
        unique_together = ('product', 'name')

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        # You can add custom save logic if needed (e.g., logging, updating related products)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_main:
            existing_main = ProductImage.objects.filter(product=self.product, is_main=True).exclude(id=self.id).first()
            if existing_main:
                raise ValidationError(f'Product {self.product.name} already has a main image (ID: {existing_main.id}). Unset it before setting a new main image.')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Image for {self.product.name}{" (Main)" if self.is_main else ""}'

class VariationImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='variations/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_main = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_main:
            existing_main = VariationImage.objects.filter(variation=self.variation, is_main=True).exclude(id=self.id).first()
            if existing_main:
                raise ValidationError(
                    f'Variation {self.variation} already has a main image (ID: {existing_main.id}). '
                    'Unset it before setting a new main image.'
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Image for {self.variation}{" (Main)" if self.is_main else ""}'

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Review by {self.buyer.username} for {self.product.name}' 
