# from django.urls import path, re_path
# from .views import (
#     UserRegistrationView, UserLoginView,
#     EmailVerificationView, PhoneVerificationView,
#     ResendVerificationView, UserProfileView,
#     send_otp, verify_otp
# )
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
#
#
# schema_view = get_schema_view(
#    openapi.Info(
#       title="Errand Tribe API",
#       default_version='v1',
#       description="API documentation for Errand Tribe project",
#        terms_of_service="https://www.google.com/policies/terms/",
#        contact=openapi.Contact(email="contact@errand.local"),
#        license=openapi.License(name="BSD License"),
#    ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )
#
# urlpatterns = [
#     path('register/', UserRegistrationView.as_view(), name='register'),
#     path('login/', UserLoginView.as_view(), name='login'),
#     path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
#     path('verify-phone/', PhoneVerificationView.as_view(), name='verify-phone'),
#     path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
#     path('profile/', UserProfileView.as_view(), name='profile'),
#     path("send-otp/", send_otp, name="send_otp"),
#     path("verify-otp/", verify_otp, name="verify_otp"),
#
#     path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
# ]
