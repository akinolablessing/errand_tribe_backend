
from rest_framework_simplejwt.tokens import RefreshToken
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.db import transaction
from .models import User
from .utils import send_email_otp, send_sms_otp, generate_otp, set_verification_tokens

from django.utils import timezone


from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    EmailVerificationSerializer, PhoneVerificationSerializer,
    UserProfileSerializer
)
from .utils import (
  send_verification_email, send_verification_sms,
     is_token_expired
)
import logging

logger = logging.getLogger(__name__)



@csrf_exempt
def send_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    email = data.get("email")
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    send_email_otp(email)
    return JsonResponse({"message": "OTP sent successfully to email"})



class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                user = serializer.save()

                email_otp = send_email_otp(user.email)
                phone_otp = send_sms_otp(str(user.phone_number))

                # Store OTPs for verification
                set_verification_tokens(user, email_otp, phone_otp)

                # Return success response
                return Response(
                    {
                        'success': True,
                        'message': 'Registration successful. Please verify your email and phone.',
                        'data': {
                            'user_id': user.id,
                            'email': user.email,
                            'phone_number': str(user.phone_number),
                            'verification_sent': {
                                'email': True,
                                'sms': True
                            }
                        }
                    },
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserLoginView(generics.GenericAPIView):

    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }
        }, status=status.HTTP_200_OK)


class EmailVerificationView(generics.GenericAPIView):
    """Email verification endpoint"""
    serializer_class = EmailVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        code = serializer.validated_data['code']

        if user.email_verified:
            return Response({
                'success': False,
                'message': 'Email already verified'
            }, status=status.HTTP_400_BAD_REQUEST)

        if (user.email_verification_token != code or
                is_token_expired(user.email_token_expires)):
            return Response({
                'success': False,
                'message': 'Invalid or expired verification code'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify email
        user.email_verified = True
        user.email_verification_token = None
        user.email_token_expires = None
        user.update_verification_status()

        return Response({
            'success': True,
            'message': 'Email verified successfully',
            'data': {
                'email_verified': True,
                'is_fully_verified': user.is_verified
            }
        }, status=status.HTTP_200_OK)


class PhoneVerificationView(generics.GenericAPIView):

    serializer_class = PhoneVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        code = serializer.validated_data['code']

        if user.phone_verified:
            return Response({
                'success': False,
                'message': 'Phone already verified'
            }, status=status.HTTP_400_BAD_REQUEST)

        if (user.phone_verification_token != code or
                is_token_expired(user.phone_token_expires)):
            return Response({
                'success': False,
                'message': 'Invalid or expired verification code'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.phone_verified = True
        user.phone_verification_token = None
        user.phone_token_expires = None
        user.update_verification_status()

        return Response({
            'success': True,
            'message': 'Phone verified successfully',
            'data': {
                'phone_verified': True,
                'is_fully_verified': user.is_verified
            }
        }, status=status.HTTP_200_OK)


class ResendVerificationView(generics.GenericAPIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        verification_type = request.data.get('type')  # 'email' or 'phone'

        if verification_type == 'email' and not user.email_verified:
            otp = generate_otp()
            set_verification_tokens(user, email_otp=otp)
            email_sent = send_verification_email(user, otp)

            return Response({
                'success': True,
                'message': 'Email verification code sent',
                'data': {'email_sent': email_sent}
            }, status=status.HTTP_200_OK)

        elif verification_type == 'phone' and not user.phone_verified:
            otp = generate_otp()
            set_verification_tokens(user, phone_otp=otp)
            sms_sent = send_verification_sms(user, otp)

            return Response({
                'success': True,
                'message': 'Phone verification code sent',
                'data': {'sms_sent': sms_sent}
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Invalid verification type or already verified'
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


# Temporary in-memory storage (better to save in DB for production)
otp_storage = {}

# @csrf_exempt
# def send_otp(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         email = data.get("email")
#
#         if not email:
#             return JsonResponse({"error": "Email is required"}, status=400)
#
#         otp = generate_otp()
#         otp_storage[email] = otp   # Save OTP temporarily
#
#         subject = "Your OTP Code"
#         message = f"Your OTP code is {otp}. It will expire in 5 minutes."
#
#         send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
#
#         return JsonResponse({"message": "OTP sent successfully to email"})
#
#     return JsonResponse({"error": "Invalid request method"}, status=405)
#

@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        data = json.loads(request.body)
        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            return JsonResponse({"error": "Email and OTP are required"}, status=400)

        if otp_storage.get(email) == otp:
            del otp_storage[email]
            return JsonResponse({"message": "OTP verified successfully"})
        else:
            return JsonResponse({"error": "Invalid or expired OTP"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)
