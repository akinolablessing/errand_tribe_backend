from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path

from authentication.views import (
    get_started,
    signup,
    create_password,
    login_view,
    forgot_password,
    reset_password,
    verify_email_otp,
    resend_email_otp,
    VerifyIdentityView,
    DocumentTypesView,
    UploadPictureView,
    LocationPermissionView,
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
      default_version="v1",
      description="API documentation for Errand Tribe project",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@errand.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)


def health_check(request):
    return JsonResponse({"status": "API is running 🚀"})


urlpatterns = [
    path("admin/", admin.site.urls),

    # -------- Auth & Users --------
    path("auth/start/", get_started, name="auth-start"),
    path("auth/signup/", signup, name="auth-signup"),
    path("auth/login/", login_view, name="auth-login"),
    path("users/<uuid:user_id>/password/set/", create_password, name="user-password-set"),
    path("auth/password/forgot/", forgot_password, name="auth-password-forgot"),
    path("users/<uuid:user_id>/password/reset/", reset_password, name="user-password-reset"),

    path("auth/email/otp/send/", resend_email_otp, name="auth-email-otp-send"),
    path("auth/email/otp/verify/", verify_email_otp, name="auth-email-otp-verify"),

    path("identity/verify/", VerifyIdentityView.as_view(), name="identity-verify"),
    path("documents/types/", DocumentTypesView.as_view(), name="document-types"),
    path("documents/upload/", UploadPictureView.as_view(), name="document-upload"),

    path("location/permission/", LocationPermissionView.as_view(), name="location-permission"),

    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    re_path(r"^docs/swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("docs/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("docs/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),

    path("health/", health_check, name="health-check"),

    path("auth/", include("authentication.urls")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
