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
    # WithdrawalMethodListCreateView,
    # WithdrawalMethodDetailView,
    # FundWalletView,
    create_flutterwave_payment,
    verify_flutterwave_payment, TermsAndConditionView,


)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static

from dashboard.views import CreateTaskView, SupermarketRunCreateView, StartTaskJourneyView, PickupDeliveryCreateView, \
    ErrandImageUploadView, CareTaskCreateView, VerificationTaskCreateView, UserTierView, PostedErrandsView, \
    ErrandDetailView, RecommendedTasksView, AvailableTasksView, ApplyErrandView, ErrandApplicationsListView, \
    UpdateApplicationStatusView, ReviewRunnerView, AppliedRunnerDetailsView

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

    path("auth/get-started/", get_started, name="get-started"),
    path("auth/signup/", signup, name="signup"),
    path("auth/login/", login_view, name="login"),
    path("users/<uuid:user_id>/set-password/", create_password, name="set-password"),
    path("auth/forgot-password/", forgot_password, name="forgot-password"),
    path("users/<uuid:user_id>/reset-password/", reset_password, name="reset-password"),

    path("auth/email/send-otp/", resend_email_otp, name="request-new-otp"),

    path("auth/email/verify/", verify_email_otp, name="verify-otp"),

    path("verify-identity/<uuid:user_id>/", VerifyIdentityView.as_view(), name="identity-verification"),
    path("documents/types/", DocumentTypesView.as_view(), name="document-types"),
    path("users/<uuid:user_id>/upload-picture/", UploadPictureView.as_view(), name="upload-picture"),

    path('users/<uuid:user_id>/location-permission/', LocationPermissionView.as_view(), name='location-permission'),

    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # path("users/<uuid:user_id>/withdrawal-methods/", WithdrawalMethodListCreateView.as_view(),name="withdrawal-methods"),
    # path("users/<uuid:user_id>/withdrawal-methods/<uuid:pk>/", WithdrawalMethodDetailView.as_view(),name="withdrawal-method-detail"),

    # path("users/<uuid:user_id>/fund-wallet/", FundWalletView.as_view(), name="fund-wallet"),

    path("api/flutterwave/create-payment/", create_flutterwave_payment, name="create-payment"),
    path("api/flutterwave/verify-payment/", verify_flutterwave_payment, name="verify-payment"),

    path("users/<uuid:user_id>/terms/", TermsAndConditionView.as_view(), name="terms-and-conditions"),

    path("api/tasks/start-tasks/", StartTaskJourneyView.as_view(), name="start-task-journey"),

    path("api/tasks/create/local-micro", CreateTaskView.as_view(), name="local-micro-create-task"),

   path('api/supermarket-run/', SupermarketRunCreateView.as_view(), name='supermarket-run-create'),

    path('api/errands/pickup-delivery/', PickupDeliveryCreateView.as_view(), name='pickup-delivery-create'),
    path('api/errands/upload-image/', ErrandImageUploadView.as_view(), name='upload-errand-image'),

    path('api/care-tasks/', CareTaskCreateView.as_view(), name='create-care-task'),

    path('api/verification-tasks/', VerificationTaskCreateView.as_view(), name='create-verification-task'),

    path('api/user/tier/', UserTierView.as_view(), name='user-tier'),

    path('posted-errands/', PostedErrandsView.as_view(), name='posted-errands'),

    path('errand/<int:id>/', ErrandDetailView.as_view(), name='errand-detail'),

    path('api/tasks/recommended/', RecommendedTasksView.as_view(), name='recommended-tasks'),
    path('api/tasks/available/', AvailableTasksView.as_view(), name='available-tasks'),

    path('errands/<uuid:errand_id>/apply/', ApplyErrandView.as_view(), name='apply-errand'),
    path('errands/<uuid:errand_id>/applications/', ErrandApplicationsListView.as_view(), name='errand-applications'),
    path('applications/<uuid:application_id>/status/', UpdateApplicationStatusView.as_view(), name='update-application-status'),

    path("applications/<int:application_id>/review/", ReviewRunnerView.as_view(), name="review-runner"),
    path("applications/<int:application_id>/runner-details/",AppliedRunnerDetailsView.as_view(),name="runner-details"),
    re_path(r"^docs/swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0), name="schema-json"),

    path("docs/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("docs/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),

    path("health/", health_check, name="health-check"),

    path("auth/", include("authentication.urls")),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
