from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (AddressSerializer, CustomTokenObtainPairSerializer,
    PasswordUpdateSerializer, UserUpdateSerializer, UserWithProfileAndAddressSerializer)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import CustomUser,  VerifiedEmail, EmailVerificationCode, UserProfile
from .serializers import UserSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import uuid, random, string
from django.utils.text import slugify

def generate_unique_username(base_username, max_length=150):
    """
    Generate a unique username by appending numbers or random strings
    """
    # Try the original username first
    if not CustomUser.objects.filter(username=base_username).exists():
        return base_username
    
    # Method 1: Append incremental numbers
    counter = 1
    while counter <= 999:  # Limit to prevent infinite loop
        new_username = f"{base_username}-{counter}"
        if len(new_username) <= max_length and not CustomUser.objects.filter(username=new_username).exists():
            return new_username
        counter += 1
    
    # Method 2: If numbers don't work, append random string
    for _ in range(10):  # Try 10 random combinations
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        new_username = f"{base_username}_{random_suffix}"
        if len(new_username) <= max_length and not CustomUser.objects.filter(username=new_username).exists():
            return new_username
    
    # Method 3: Last resort - use timestamp
    import time
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    return f"{base_username}_{timestamp}"

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


@api_view(['POST'])
@permission_classes([AllowAny])
def request_email_verification(request):
    email = request.data.get('email')

    # Validate email is present
    if not email:
        return Response({'error': 'Email is required'}, status=400)

    # Validate format
    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "Invalid email format"}, status=400)

    # Check if email already verified
    if VerifiedEmail.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=409)

    try:
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Delete any existing verification codes for this email
        EmailVerificationCode.objects.filter(email=email).delete()
        
        # Store verification code with expiration (15 minutes)
        expiry_time = timezone.now() + timedelta(minutes=15)
        EmailVerificationCode.objects.create(
            email=email,
            code=verification_code,
            expires_at=expiry_time
        )

        # Send verification code via email
        send_mail(
            subject="Your verification code",
            message=f"Your verification code is: {verification_code}\n\nThis code will expire in 15 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({'message': 'Verification code sent!'}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

    
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    email = request.data.get('email')
    code = request.data.get('code')

    if not email or not code:
        return Response({'error': 'Email and verification code are required'}, status=400)

    try:
        # Find the verification code
        verification_record = EmailVerificationCode.objects.get(
            email=email,
            code=code
        )
        
        # Check if code has expired
        if timezone.now() > verification_record.expires_at:
            verification_record.delete()  # Clean up expired code
            return Response({'error': 'Verification code has expired'}, status=400)
        
        # Code is valid, save to VerifiedEmail table
        VerifiedEmail.objects.get_or_create(email=email)
        
        # Delete the verification code after successful verification
        verification_record.delete()

        return Response({'message': 'Email verified successfully'}, status=200)
        
    except EmailVerificationCode.DoesNotExist:
        return Response({'error': 'Invalid verification code'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# Optional: API endpoint to resend verification code
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email is required'}, status=400)
    
    # Check if there's a pending verification for this email
    if not EmailVerificationCode.objects.filter(email=email).exists():
        return Response({'error': 'No pending verification found for this email'}, status=400)
    
    # Check if email already verified
    if CustomUser.objects.filter(email=email).exists():
        return Response({"error": "Email already used"}, status=409)

    
    try:
        # Generate new verification code
        verification_code = generate_verification_code()
        
        # Update existing record with new code and expiry
        expiry_time = timezone.now() + timedelta(minutes=15)
        EmailVerificationCode.objects.filter(email=email).update(
            code=verification_code,
            expires_at=expiry_time,
            created_at=timezone.now()
        )
        
        # Send new verification code
        send_mail(
            subject="Your new verification code",
            message=f"Your verification code is: {verification_code}\n\nThis code will expire in 15 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response({'message': 'New verification code sent!'}, status=200)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def signup(request):
    email = request.data.get('email')
    password = request.data.get('password')
    username = request.data.get('username')
    contact_no = request.data.get('contact_no')
    
    # 1. Check if email is valid
    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Check if email is verified
    if not VerifiedEmail.objects.filter(email=email).exists():
        return Response({"error": "Email is not verified."}, status=status.HTTP_403_FORBIDDEN)
    
    # 3. Check if user with email already exists
    if CustomUser.objects.filter(email=email).exists():
        return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    # 4. Generate unique username
    unique_username = generate_unique_username(username)
    original_username = username
    
    try:
        # 5. Create user with unique username
        user = CustomUser.objects.create_user(
            email=email,
            username=unique_username,
            contact_no=contact_no,
            role='buyer',
            password=password,
        )
        
        # 6. Create user profile
        profile = UserProfile.objects.create(
            user=user,
            full_name=request.data.get('full_name', ''),
            profile_picture='',
        )

        # 7. Create address (optional)
        address_data = request.data.get('address')
        if address_data:
            address_serializer = AddressSerializer(data=address_data)
            if address_serializer.is_valid():
                address_serializer.save(user=user)
            else:
                return Response(
                    {"error": "Address is invalid", "details": address_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 8. Return response with success message
        user_data = UserSerializer(user).data
        response_data = {
            "message": "User created successfully",
            "user": user_data,
            "user_id": user.id
        }
        
        # Inform user if username was changed
        if unique_username != original_username:
            response_data["username_changed"] = True
            response_data["original_username"] = original_username
            response_data["new_username"] = unique_username
            response_data["message"] = f"User created successfully. Username changed from '{original_username}' to '{unique_username}' as the original was taken."
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except IntegrityError as e:
        return Response(
            {"error": "User creation failed due to database constraint"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": "An unexpected error occurred during user creation"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class Login(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response(
                {"error": f"Invalid credentialzs. {e}. Please check your email and password."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": f"Invalid credentialx. {e}. Please check your email and password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "message": "You have access to this protected view!",
            "user_email": request.user.email,
            "user_id": str(request.user.id)
        })
        
class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserWithProfileAndAddressSerializer(user)
        return Response(serializer.data)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"success": "Logged out successfully"}, status=status.HTTP_205_RESET_CONTENT)
        else:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    updated_user = serializer.save()
                    
                    # Return updated user data
                    response_serializer = UserWithProfileAndAddressSerializer(updated_user)
                    return Response({
                        'message': 'Profile updated successfully',
                        'user': response_serializer.data
                    }, status=status.HTTP_200_OK)
                    
            except Exception as e:
                return Response({
                    'error': 'An error occurred while updating profile',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class PasswordUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        serializer = PasswordUpdateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'message': 'Password updated successfully'
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'error': 'An error occurred while updating password',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)