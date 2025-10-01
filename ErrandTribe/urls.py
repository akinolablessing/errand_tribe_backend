from django.urls import path
from django.contrib import admin
from authentication.views import (
    get_started,
    signup,
    create_password,
    login_view,
    forgot_password,
    reset_password,
    # send_otp_util,
    verify_email_otp,
    resend_email_otp,
    VerifyIdentityView,
    DocumentTypesView, UploadPictureView, LocationPermissionView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static

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
    path("email/send-otp/", resend_email_otp),
    path("email/verify-otp/", verify_email_otp),

    path("verify_identity/", VerifyIdentityView.as_view(), name="verify_identity" ),
    path("document-type/", DocumentTypesView.as_view(), name="document-types" ),
    path("upload-picture/", UploadPictureView.as_view(), name="upload-picture"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("location-permission/", LocationPermissionView.as_view(), name="location-permission"),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)