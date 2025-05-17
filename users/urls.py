from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainPairView, request_email_verification, verify_email, signup


urlpatterns = [
    path('login/', 
         CustomTokenObtainPairView.as_view(), 
         name='token_obtain_pair'),
    path('api/token/refresh/', 
        TokenRefreshView.as_view(), 
        name='token_refresh'),
    path("request-verification/", 
          request_email_verification,
          name="request-verification"),
    path("verify-email/", 
          verify_email,
          name="verify-email"),
    path("signup/",
          signup,
          name="signup"),
]
