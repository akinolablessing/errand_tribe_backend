import random

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .utils import send_email_otp as send_otp_util
from django.utils.decorators import method_decorator
from ErrandTribe import settings
from .serializers import (
    SignupSerializer,
    PasswordSerializer,
    LoginSerializer,
    EmailOTPSerializer, IdentityVerificationSerializer, UploadPictureSerializer, LocationPermissionSerializer,
)

User = get_user_model()


def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


@api_view(["GET"])
@permission_classes([AllowAny])
def get_started(request):
    return Response({"next": "role_selection", "roles": ["runner", "tasker"]})

@swagger_auto_schema(
    method="post",
    request_body=SignupSerializer,
    responses={201: "User created", 400:"Validation error"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        try:
            otp = send_otp_util(user)

            return Response(
                {
                    "message": f"Hi {user.first_name},\n\nYour OTP code is: {otp}\nIt will expire in 30 minutes.",
                    "user_id": str(user.id),
                },
                status=201,
            )
        except Exception as e:
            return Response(
                {
                    "message": "User created, but OTP email failed.",
                    "user_id": str(user.id),
                    "otp_sent": False,
                    "error": str(e),
                },
                status=201,
            )

    return Response(serializer.errors, status=400)
@swagger_auto_schema(
    method="post",
    request_body=PasswordSerializer,
    manual_parameters=[
        openapi.Parameter(
            'user_id',
            openapi.IN_PATH,
            description="User ID (UUID)",
            type=openapi.TYPE_STRING
        )
    ],
    responses={200: "Password created successfully", 404: "User not found"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_password(request, user_id):
    serializer = PasswordSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = User.objects.get(id=user_id)
            user.set_password(serializer.validated_data["password"])
            user.save()
            return Response({"message": "Password created successfully"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(
    method="post",
    request_body=LoginSerializer,
    responses={200: "Login successful", 403: "Email not verified", 400: "Invalid credentials"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        if not user.is_email_verified:
            return Response(
                {"error": "Please verify your email before login."}, status=403
            )
        tokens = generate_tokens_for_user(user)
        return Response({"message": "Login successful", "tokens": tokens})
    return Response(serializer.errors, status=400)

@swagger_auto_schema(
    method="post",
    request_body=EmailOTPSerializer,
    responses={200: "Password reset OTP sent", 404: "User not found", 400: "Validation error"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    serializer = EmailOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            user.set_email_otp(otp)
            # TODO: send via email
            return Response({"message": "Password reset OTP sent"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(
    method="post",
    request_body=PasswordSerializer,
    responses={200: "Password reset successful", 404: "User not found", 400: "Invalid or expired OTP"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request, user_id):
    otp = request.data.get("otp")
    serializer = PasswordSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = User.objects.get(id=user_id)
            if not user.verify_email_otp(otp):
                return Response({"error": "Invalid or expired OTP"}, status=400)
            user.set_password(serializer.validated_data["password"])
            user.save()
            return Response({"message": "Password reset successful"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(
    method="post",
    request_body=EmailOTPSerializer,
    responses={
        200: "OTP resent successfully",
        404: "User not found",
        400: "Validation error",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def resend_email_otp(request):

    serializer = EmailOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            otp = send_otp_util(user)
            return Response({
                "message": f"OTP resent successfully to {email}",
                "otp": otp if settings.DEBUG else "Sent via email"
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(
    method="post",
    request_body=EmailOTPSerializer,
    responses={200: "Email verified successfully", 404: "User not found", 400: "Invalid or expired OTP"},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_otp(request):
    serializer = EmailOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        otp = serializer.validated_data.get("otp")
        try:
            user = User.objects.get(email=email)
            if user.verify_email_otp(otp):
                return Response({"message": "Email verified successfully"})
            return Response({"error": "Invalid or expired OTP"}, status=400)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
    return Response(serializer.errors, status=400)


DOCUMENT_TYPES_BY_COUNTRY = {
    "Nigeria": ["National ID", "Driver's License", "Passport"],
    "Kenya": ["National ID", "Driver's License", "Passport", "Alien Card"],
    "Togo": ["National ID", "Driver's License", "Passport", "Carte Nationale d'Identite"],
    "Ghana": ["National ID", "Driver's License", "Passport"]
}

class DocumentTypesView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('country', openapi.IN_QUERY, description="Country name", type=openapi.TYPE_STRING)
        ],
        operation_description="Fetch valid document types by country",
        responses={200: "Success", 400: "Invalid country"}
    )
    def get(self, request):
        country = request.GET.get("country")
        if not country:
            return Response({"error": "Country parameter is required."}, status=400)

        types = DOCUMENT_TYPES_BY_COUNTRY.get(country)
        if types:
            return Response({"country": country, "document_types": types})
        return Response({"error": "Unsupported country."}, status=400)

class VerifyIdentityView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=IdentityVerificationSerializer,
        operation_description="Upload identity document for verification",
        responses={201: "Verification submitted", 400: "Validation error"}
    )
    def post(self, request):
        serializer = IdentityVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Verification submitted"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UploadPictureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=UploadPictureSerializer,
        operation_description="Upload or update user profile picture",
        responses={200: "Profile picture uploaded", 400: "Validation error"}
    )
    def post(self, request):
        serializer = UploadPictureSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile picture uploaded successfully",
                "profile_picture_url": request.user.profile_picture.url if request.user.profile_picture else None
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=LocationPermissionSerializer,
        operation_description="Enable location with options: 'while_using_app' or 'always'",
        responses={200: "Location permission updated", 400: "Validation error"}
    )
    def post(self, request):
        serializer = LocationPermissionSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Location permission updated successfully",
                "location_permission": request.user.location_permission
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        return Response({
            "location_permission": request.user.location_permission
        }, status=status.HTTP_200_OK)