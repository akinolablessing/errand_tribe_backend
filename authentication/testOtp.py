from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
import random


def send_otp_email(request):
    # Generate OTP
    otp = str(random.randint(100000, 999999))

    # Email details
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. It will expire in 5 minutes.'
    recipient_email = 'recipient@example.com'  # Replace with user's email

    # Send email
    send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient_email])

    return JsonResponse({'message': 'OTP sent successfully', 'otp': otp})
