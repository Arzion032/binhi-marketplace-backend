from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, contact_no, role, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            contact_no=contact_no,
            role=role,
        )
        user.set_password(password)  # This hashes the password
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
    contact_no = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'  # Login using email
    REQUIRED_FIELDS = ['username', 'contact_no']  # Required fields for createsuperuser
    
    def __str__(self):
        return self.username
        

# This is the User Profiles   
class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='profile')  
    full_name = models.TextField(blank=False, null=False)
    address = models.TextField(blank=False, null=False)
    profile_picture = models.TextField(blank=False, null=False)
    other_details = models.JSONField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
    
class VerifiedEmail(models.Model):
    email = models.EmailField(unique=True)
    verified_at = models.DateTimeField(auto_now_add=True)
