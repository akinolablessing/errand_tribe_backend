from django.urls import path
from django.contrib import admin
from authentication.views import (
    get_started,
    signup,
    create_password,
    login_view,
    forgot_password,
    reset_password,
    send_email_otp,
    verify_email_otp,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Errand Tribe API",
      default_version='v1',
      description="API documentation for Errand Tribe project",
       terms_of_service="https://www.google.com/policies/terms/",
       contact=openapi.Contact(email="contact@errand.local"),
       license=openapi.License(name="BSD License"),
   ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("get-started/", get_started),
    path("signup/", signup),
    path("users/<uuid:user_id>/create-password/", create_password),
    path("login/", login_view),
    path("forgot-password/", forgot_password),
    path("users/<uuid:user_id>/reset-password/", reset_password),
    path("email/send-otp/", send_email_otp),
    path("email/verify-otp/", verify_email_otp),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
