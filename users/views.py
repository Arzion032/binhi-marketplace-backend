from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import CustomUser,  VerifiedEmail
from .serializers import UserSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
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
            is_approved = True,
            is_active = True,
            is_rejected = False
        )
        
        # 5. Return serialized user without password
        user_data = UserSerializer(user).data
        return Response({
            "message": "User created successfully",
            "user": user_data,
            "user_id": user_data['id']
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):

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
    
