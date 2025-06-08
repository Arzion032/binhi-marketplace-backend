from .models import CustomUser, UserProfile, Address, VerifiedEmail
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'     
        
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        
class UserWithProfileSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = '__all__'
        
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'region',
            'province',
            'city',
            'barangay',
        ]

class UserWithProfileAndAddressSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = '__all__'
        
class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['contact_no', 'username', 'password', 'email', 'role']
        

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token["email"] = user.email
        token["role"] = user.role
        token["username"] = user.username
        return token
        
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add extra responses here
        data.update({
            "user_id": str(self.user.id),
            "email": self.user.email,
            "role": self.user.role,
            "username": self.user.username
        })
        
        return data
    
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['full_name']
        
    def validate_full_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Full name cannot be empty.")
        return value.strip()

class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['region', 'province', 'city', 'barangay']
        
    def validate(self, data):
        # Ensure all address fields are provided
        required_fields = ['region', 'province', 'city', 'barangay']
        for field in required_fields:
            if not data.get(field) or not data.get(field).strip():
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required.")
        return data

class UserUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileUpdateSerializer()
    address = AddressUpdateSerializer()
    
    class Meta:
        model = CustomUser
        fields = ['email', 'contact_no', 'profile', 'address']
        
    def validate_email(self, value):
        # Check if email is already taken by another user
        if CustomUser.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value
        
    def validate_contact_no(self, value):
        # Check if contact number is already taken by another user
        if CustomUser.objects.filter(contact_no=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("This contact number is already in use.")
        return value
    
    def is_valid(self, raise_exception=False):
        result = super().is_valid(raise_exception=False)
        print(f"DEBUG: Serializer errors: {self.errors}")
        if raise_exception and not result:
            raise serializers.ValidationError(self.errors)
        return result
    
    def update(self, instance, validated_data):
        # Extract nested data
        profile_data = validated_data.pop('profile', {})
        address_data = validated_data.pop('address', {})
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create profile - ALWAYS create if doesn't exist
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'full_name': profile_data.get('full_name', ''),
                    'profile_picture': '',  # Set default empty string
                }
            )
            # If profile already exists, update it
            if not created:
                for attr, value in profile_data.items():
                    setattr(profile, attr, value)
                profile.save()
            # If profile was just created, update any additional fields
            elif len(profile_data) > 1 or profile_data.get('full_name') != profile.full_name:
                for attr, value in profile_data.items():
                    setattr(profile, attr, value)
                profile.save()
        
        # Update or create address (assuming user has one primary address)
        if address_data:
            address = instance.addresses.first()
            if address:
                for attr, value in address_data.items():
                    setattr(address, attr, value)
                address.save()
            else:
                # Create new address if none exists
                Address.objects.create(user=instance, **address_data)
        
        return instance
    
    
class PasswordUpdateSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        # Use Django's built-in password validation
        validate_password(value)
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Password confirmation does not match."
            })
        
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': "New password must be different from current password."
            })
        
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user