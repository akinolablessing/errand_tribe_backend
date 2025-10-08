

from django.http import JsonResponse
from django.urls import path, include

from authentication import views

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
def health_check(request):
    return JsonResponse({"status": "API is running 🚀"})
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)