from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid

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
    
    def __str__(self):
        return self.username
        

# This is the User Profiles   
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='profile')  
    full_name = models.TextField(blank=False, null=False)
    profile_picture = models.TextField(blank=False, null=False)
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
    street_address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=10, blank=True)   
    landmark = models.CharField(max_length=255, blank=True)     
   

    def __str__(self):
        return f"{self.user.username}: {self.street_address}, {self.barangay}, {self.city}"


# NOTE:
# The Address model below is commented out for now to simplify the MVP/user profile logic.
# Currently, we are storing address and contact information directly in the UserProfile model.
# If we need to support multiple addresses per user, address management, or integration with couriers,
# uncomment and migrate this model, then refactor the codebase to use Address objects instead.
#
# Leaving this model here for future expansion and easier transition to a scalable address system.

# class Address(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
#     full_name = models.CharField(max_length=100)
#     phone_number = models.CharField(max_length=20)
#     region = models.CharField(max_length=50)
#     province = models.CharField(max_length=50)
#     city = models.CharField(max_length=50)
#     barangay = models.CharField(max_length=100)
#     street_address = models.CharField(max_length=255)
#     landmark = models.CharField(max_length=255, blank=True)
#     address_type = models.CharField(
#         max_length=20, 
#         choices=[('home', 'Home'), ('work', 'Work'), ('other', 'Other')], 
#         blank=True
#     )
#     is_default = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     def __str__(self):
#         return f"{self.full_name} ({self.street_address}, {self.barangay}, {self.city})"
