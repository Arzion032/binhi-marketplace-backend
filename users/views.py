import django.shortcuts
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (AddressSerializer, CustomTokenObtainPairSerializer,
    PasswordUpdateSerializer, UserUpdateSerializer, UserWithProfileAndAddressSerializer)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import CustomUser,  VerifiedEmail
from .serializers import UserSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import uuid


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
        # Generate and send verification token
        token = str(uuid.uuid4())  # Demo token, not stored

        verification_link = f"http://localhost:8001/users/verify-email/?token={token}&email={email}"

        send_mail(
            subject="Verify your email",
            message=f"Click the link to verify: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({'message': 'Verification link sent!'}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

    
@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request):
    email = request.GET.get('email')
    # token = request.GET.get('token')  # add token checking here

    if not email:
        return Response({'error': 'Invalid request'}, status=400)

    # Save to VerifiedEmail table
    VerifiedEmail.objects.get_or_create(email=email)

    return Response({'message': 'Email verified successfully'}, status=200)

    
@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def signup(request):
    email = request.data.get('email')

    # 1. Check if email is valid
    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "Invalid email format"}, status=400)

    # 2. Check if email is verified
    if not VerifiedEmail.objects.filter(email=email).exists():
        return Response({"error": "Email is not verified."}, status=status.HTTP_403_FORBIDDEN)
    
    # 3. Validate user data
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # 4. Create user with proper password hashing
        user = CustomUser.objects.create_user(
            email=serializer.validated_data['email'],
            username=serializer.validated_data['username'],
            contact_no=serializer.validated_data['contact_no'],
            role='buyer',
            password=request.data.get('password'),
        )

        # 5. Create address (optional: check if address data exists in request)
        address_data = request.data.get('address')
        if address_data:
            address_serializer = AddressSerializer(data=address_data)
            if address_serializer.is_valid():
                address_serializer.save(user=user)
            else:
                # Clean up by deleting user if address fails
                user.delete()
                return Response(
                    {"error": "Address is invalid", "details": address_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # 6. Return serialized user without password
        user_data = UserSerializer(user).data
        return Response({
            "message": "User created successfully",
            "user": user_data,
            "user_id": user_data['id']
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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