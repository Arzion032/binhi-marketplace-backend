from django.db import models
from django.conf import settings
from products.models import Product, ProductVariation
from django.utils import timezone
from users.models import CustomUser
import uuid, string, random
   
    
class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_identifier = models.CharField(max_length=20, unique=True, blank=True, null=True)  # New field for readable identifier
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    delivery_method = models.CharField(max_length=50, null=True, blank=True)
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_random_string(self, length=8):
        """Generate a random string of uppercase letters."""
        letters = string.ascii_uppercase
        return ''.join(random.choice(letters) for i in range(length))

    def save(self, *args, **kwargs):
        if not self.order_identifier:
            today = timezone.now().date()
            formatted_date = today.strftime("%y%m%d")  # Format as 'yymmdd'

            # Generate the random string of letters
            random_string = self.generate_random_string()

            # Set the order_identifier in the required format
            self.order_identifier = f'{formatted_date}{random_string}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order {self.id} by {self.buyer.username}'

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, default=None)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.quantity}x {self.variation.name} in Order {self.order.id}'

class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Order status histories'

    def __str__(self):
        return f'Order {self.order.id} status changed to {self.status}'

class MarketTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='transaction')
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sales')
    payment_method = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Transaction {self.id} for Order {self.order.id}'
