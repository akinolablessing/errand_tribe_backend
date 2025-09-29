import random

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from .utils import send_email_otp

from ErrandTribe import settings
from .serializers import (
    SignupSerializer,
    PasswordSerializer,
    LoginSerializer,
    EmailOTPSerializer,
)

User = get_user_model()


def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


@api_view(["GET"])
@permission_classes([AllowAny])
def get_started(request):
    return Response({"next": "role_selection", "roles": ["runner", "tasker"]})


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        try:
            # otp = str(random.randint(100000, 999999))
            send_email_otp(user)
            print("send_email_otp function is:", send_email_otp)
            print("user.set_email_otp method is:", user.set_email_otp)

            return  Response(
            {
                "message": f"Hi {user.first_name},\n\nYour OTP code is: {user.otp}\nIt will expire in 30 minutes.",
                "user_id": str(user.id),
            },
            status=201,
        )


        # try:
        #     send_mail(
        #         subject="Verify your email - ErrandTribe",
        #         message=f"Hi {user.first_name},\n\nYour OTP code is: {otp}\nIt will expire in 30 minutes.",
        #         from_email=settings.DEFAULT_FROM_EMAIL,
        #         recipient_list=[user.email],
        #         fail_silently=False,
        #     )
        #     email_status = f"We've sent an OTP with an activation code to your email {user.email}"

        except Exception as e:

            return Response(

                {"message": "User created, but OTP email failed.", "error": str(e)},

                status=status.HTTP_201_CREATED,

            )
        # return Response(
        #     {
        #         "message": email_status,
        #         "user_id": str(user.id),
        #     },
        #     status=201,
        # )

    return Response(serializer.errors, status=400)

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


@api_view(["POST"])
@permission_classes([AllowAny])
def send_email_otp(request):
    serializer = EmailOTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            user.set_email_otp(otp)
            # TODO: send via email
            return Response({"message": f"OTP sent to {email}"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
    return Response(serializer.errors, status=400)


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
