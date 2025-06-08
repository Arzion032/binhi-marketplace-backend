from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import uuid

def generate_unique_username(instance, field_value, slug_field_name='slug'):
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

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, contact_no, role, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        
        if role == 'buyer':
            is_approved = True
            is_active = True
            is_rejected = False
        
        else:
            is_approved = False
            is_active = False
            is_rejected = False
        
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            contact_no=contact_no,
            role=role,
            is_approved = is_approved,
            is_active = is_active,
            is_rejected = is_rejected,
        )
        user.set_password(password)  
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, contact_no, password=None):
        user = self.create_user(
            email=email,
            username=username,
            contact_no=contact_no,
            role='admin',
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    username = models.TextField(unique=True)
    contact_no = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'  # Login using email
    REQUIRED_FIELDS = ['username', 'contact_no']  # Required fields for createsuperuser
    
    def save(self, *args, **kwargs):
        # Ensure username is unique
        if not self.username:
            self.username = self.email.split('@')[0]  # Set default username to part of the email
        
        # Check if the username exists in the database, and modify it if needed
        if CustomUser.objects.filter(username=self.username).exists():
            base_username = self.username
            counter = 1
            while CustomUser.objects.filter(username=self.username).exists():
                self.username = f"{base_username}{counter}"
                counter += 1

        super(CustomUser, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.username

        

# This is the User Profiles   
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='profile')  
    full_name = models.TextField(blank=True, null=True)
    profile_picture = models.TextField(blank=True, null=True)
    other_details = models.JSONField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
    
class VerifiedEmail(models.Model):
    email = models.EmailField(unique=True)
    verified_at = models.DateTimeField(auto_now_add=True)
    
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    region = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    barangay = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username}: {self.street_address}, {self.barangay}, {self.city}"

class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ['email', 'code']
        
    def __str__(self):
        return f"{self.email} - {self.code}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
