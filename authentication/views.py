import datetime
import random
from django.utils import timezone

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from . import serializers
from .models import WithdrawalMethod
from .utils import send_email_otp as send_otp_util
from ErrandTribe import settings
from .serializers import (
    SignupSerializer,
    PasswordSerializer,
    LoginSerializer,
    EmailOTPSerializer, IdentityVerificationSerializer, UploadPictureSerializer, LocationPermissionSerializer,
    WithdrawalMethodSerializer,
)
from decimal import Decimal

import os
import requests
from django.shortcuts import get_object_or_404

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
                    "message": f"We've sent an OTP with an activation code to your email:  {user.email}",
                    "user_id": str(user.id),
                    "otp_sent": True
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

        steps = [
            ("is_email_verified", "Verify your email"),
            ("is_identity_verified", "Verify your identity"),
            ("has_uploaded_picture", "Upload your profile picture"),
            ("has_enabled_location", "Enable location"),
            ("has_withdrawal_method", "Add a withdrawal method"),
            ("has_funded_wallet", "Fund your wallet"),
        ]

        for field, message in steps:
            if not getattr(user, field):
                return Response({"error": message}, status=403)
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
            print(user)
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
            if verify_otp(user,otp):
                return Response({"success":True,"message": "Email verified successfully"},status=200)
            return Response({"success":False,"error": "Invalid or expired OTP"}, status=400)
        except User.DoesNotExist:
            return Response({"success": False,"error": "User not found"}, status=404)
    return Response({"success": False, "errors": serializer.errors}, status=400)



def verify_otp(user, otp: str) -> bool:
    if not user.email_otp or  user.email_otp != str(otp):
        return False

    if user.email_otp_created_at < timezone.now() - datetime.timedelta(minutes=30):
        return False
    user.is_email_verified = True
    user.email_otp = None
    user.save(update_fields=["is_email_verified", "email_otp"])
    return True

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
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=IdentityVerificationSerializer,
        operation_description="Upload identity document for verification",
        manual_parameters=[
            openapi.Parameter(
                "user_id",
                openapi.IN_PATH,
                description="UUID of the user submitting identity verification",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            201: openapi.Response("Verification submitted"),
            400: openapi.Response("Validation error"),
            404: openapi.Response("User not found"),
        }
    )
    def post(self, request,user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = IdentityVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            user.is_identity_verified = True
            user.save(update_fields=["is_identity_verified"])
            return Response({"message": "Verification submitted"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UploadPictureView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=UploadPictureSerializer,
        operation_description="Upload or update user profile picture",
        responses={200: "Profile picture uploaded successfully", 400: "Validation error", 404:"User not found"},
    )
    def post(self, request,user_id):
        profile_picture_url = None
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"success":False,"error": "User not found"}, status=404)
        serializer = UploadPictureSerializer(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            if serializer.instance.profile_picture:
                profile_picture_url = request.build_absolute_uri(serializer.instance.profile_picture.url)

            user.has_uploaded_picture = True
            user.save(update_fields=["has_uploaded_picture"])
            return Response({
                "success": True,
                "message": "Profile picture uploaded successfully",
                "profile_picture_url": profile_picture_url
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationPermissionView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LocationPermissionSerializer,
        operation_description="Enable location with options: 'while_using_app' or 'always'",
        responses={200: "Location permission updated", 400: "Validation error", 404:"User not found"},
    )
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"success":False,"error": "User not found"}, status=404)
        serializer = LocationPermissionSerializer(instance=user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(location_permission=serializer.validated_data["location_permission"])
            if serializer.validated_data.get("location_permission"):
                user.has_enabled_location = True
                user.save(update_fields=["has_enabled_location"])
            return Response({
                "success": True,
                "message": "Location permission updated successfully",
                "location_permission": user.location_permission
            }, status=status.HTTP_200_OK)
        return Response({"success": True,"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "error": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "success": True,
            "location_permission": user.location_permission
        }, status=status.HTTP_200_OK)

class WithdrawalMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = WithdrawalMethodSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return WithdrawalMethod.objects.filter(user_id=user_id)

    @swagger_auto_schema(
        operation_description="List all withdrawal methods for the logged-in user",
        responses={200: WithdrawalMethodSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        if not User.objects.filter(id=user_id).exists():
            return Response({"success": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new withdrawal method for the logged-in user",
        request_body=WithdrawalMethodSerializer,
        responses={201: WithdrawalMethodSerializer()},
    )
    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        try:
            self.user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"success": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.user)


class WithdrawalMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WithdrawalMethodSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return WithdrawalMethod.objects.filter(user_id=user_id)

    @swagger_auto_schema(
        operation_description="Retrieve a specific withdrawal method belonging to the logged-in user",
        responses={200: WithdrawalMethodSerializer()},
    )
    def get(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        if not User.objects.filter(id=user_id).exists():
            return Response({"success": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a specific withdrawal method belonging to the logged-in user",
        request_body=WithdrawalMethodSerializer,
        responses={200: WithdrawalMethodSerializer()},
    )
    def put(self, request, *args, **kwargs):
        user_id = self.kwargs.get("user_id")
        if not User.objects.filter(id=user_id).exists():
            return Response({"success": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return super().put(request, *args, **kwargs)


class WithdrawalMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = WithdrawalMethodSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return WithdrawalMethod.objects.filter(user_id=user_id)


    def perform_create(self, serializer):
        user_id = self.kwargs.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"})
        serializer.save(user=user)
        if not user.has_withdrawal_method:
            user.has_withdrawal_method = True
            user.save(update_fields=["has_withdrawal_method"])


class WithdrawalMethodDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WithdrawalMethodSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return WithdrawalMethod.objects.filter(user_id=user_id)


class FundWalletView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Fund the user's wallet using an existing withdrawal method",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Amount to fund"),
                "withdrawal_method_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the withdrawal method"),
            },
            required=["amount", "withdrawal_method_id"],
        ),
        responses={201: "Wallet funded successfully", 400: "Validation error",404: "User or withdrawal method not found"}
    )
    def post(self, request,user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"success": False, "error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        amount = request.data.get("amount")
        withdrawal_method_id = request.data.get("withdrawal_method_id")

        if not amount or Decimal(amount) <= 0:
            return Response({"error": "Invalid amount"}, status=400)

        try:
            method = WithdrawalMethod.objects.get(id=withdrawal_method_id, user=user)
        except WithdrawalMethod.DoesNotExist:
            return Response({"error": "Withdrawal method not found"}, status=404)

        user.wallet_balance += Decimal(amount)
        if not user.has_funded_wallet:
            user.has_funded_wallet = True
        user.save(update_fields=["wallet_balance", "has_funded_wallet"])

        return Response({
            "message": "Wallet funded successfully",
            "new_balance": user.wallet_balance,
            "withdrawal_method": WithdrawalMethodSerializer(method).data
        }, status=201)


@swagger_auto_schema(
    method="post",
    operation_description="Initialize a payment using Flutterwave API",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Amount to charge"),
            "currency": openapi.Schema(type=openapi.TYPE_STRING, description="Currency, e.g., NGN"),
            "email": openapi.Schema(type=openapi.TYPE_STRING, description="Customer email"),
            "tx_ref": openapi.Schema(type=openapi.TYPE_STRING, description="Unique transaction reference"),
            "redirect_url": openapi.Schema(type=openapi.TYPE_STRING, description="Optional redirect URL after payment")
        },
        required=["amount", "currency", "email", "tx_ref"]
    ),
    responses={
        200: openapi.Response(description="Payment link created successfully"),
        400: openapi.Response(description="Validation error")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def create_flutterwave_payment(request):

    FLW_SECRET_KEY = os.environ.get("FLW_SECRET_KEY")
    url = "https://api.flutterwave.com/v3/payments"

    amount = request.data.get("amount")
    currency = request.data.get("currency", "NGN")
    email = request.data.get("email")
    tx_ref = request.data.get("tx_ref")
    redirect_url = request.data.get("redirect_url", "https://example.com/payment-success")

    if not all([amount, currency, email, tx_ref]):
        return Response({"detail": "Missing required fields"}, status=400)

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": currency,
        "redirect_url": redirect_url,
        "customer": {"email": email},
        "customizations": {
            "title": "ErrandTribe Wallet Funding",
            "description": "Fund your wallet using Flutterwave"
        }
    }

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return Response({
            "message": "Payment link created successfully",
            "payment_link": data.get("data", {}).get("link")
        }, status=200)
    except requests.RequestException as e:
        return Response({"detail": "Failed to create payment", "error": str(e)}, status=502)


@swagger_auto_schema(
    method="post",
    operation_description="Verify Flutterwave payment and credit the user's wallet",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "transaction_id": openapi.Schema(type=openapi.TYPE_STRING, description="Flutterwave transaction ID"),
            "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="UUID of user to credit"),
            "expected_amount": openapi.Schema(type=openapi.TYPE_NUMBER, description="Expected payment amount"),
        },
        required=["transaction_id", "user_id", "expected_amount"]
    ),
    responses={
        200: openapi.Response(description="Wallet credited successfully"),
        400: openapi.Response(description="Verification failed or invalid transaction"),
        404: openapi.Response(description="User not found")
    }
)
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_flutterwave_payment(request):
    FLW_SECRET_KEY = os.environ.get("FLW_SECRET_KEY")
    transaction_id = request.data.get("transaction_id")
    user_id = request.data.get("user_id")
    expected_amount = request.data.get("expected_amount")

    if not all([transaction_id, user_id, expected_amount]):
        return Response({"detail": "Missing required fields"}, status=400)

    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return Response({"detail": "Failed to contact payment provider", "error": str(e)}, status=502)

    if data.get("status") != "success":
        return Response({"detail": "Verification failed", "raw": data}, status=400)

    tx_data = data.get("data", {})
    if tx_data.get("status") != "successful":
        return Response({"detail": "Transaction not successful"}, status=400)

    charged_amount = Decimal(str(tx_data.get("amount")))
    expected_amount = Decimal(str(expected_amount))

    if charged_amount < expected_amount:
        return Response({"detail": "Charged amount less than expected"}, status=400)

    user = get_object_or_404(User, id=user_id)
    user.wallet_balance = (user.wallet_balance or Decimal("0.00")) + charged_amount
    user.has_funded_wallet = True
    user.save(update_fields=["wallet_balance", "has_funded_wallet"])

    return Response({
        "message": "Wallet funded successfully",
        "credited_amount": str(charged_amount),
        "new_balance": str(user.wallet_balance),
        "transaction_ref": tx_data.get("tx_ref")
    }, status=200)