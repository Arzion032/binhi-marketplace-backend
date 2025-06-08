from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import (Login, PasswordUpdateView, request_email_verification, signup,
      UserDetailView, UserUpdateView, verify_email, resend_verification_code)


urlpatterns = [
    path('login/', 
         Login.as_view(), 
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
    path('me/', 
         UserDetailView.as_view(), 
         name='user-detail'),
    path('me/update/', 
         UserUpdateView.as_view(), 
         name='user-update'),
    path('me/update-password/', 
         PasswordUpdateView.as_view(), 
         name='user-update-password'),
    path('request-email-verification/', 
         request_email_verification, 
         name='request_email_verification'),
    path('verify-email/', 
         verify_email, 
         name='verify_email'),
    path('resend-verification-code/', 
         resend_verification_code, 
         name='resend_verification_code'),
]
