from django.urls import path
from .views import (
    UserRegistrationView, UserLoginView,
    EmailVerificationView, PhoneVerificationView,
    ResendVerificationView, UserProfileView
)

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('verify-phone/', PhoneVerificationView.as_view(), name='verify-phone'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
