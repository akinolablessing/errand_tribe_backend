from django.utils import timezone
from twilio.rest import Client
import logging
import random
from django.core.mail import send_mail
from django.conf import settings


logger = logging.getLogger(__name__)



def generate_otp():
    return str(random.randint(100000, 999999))



otp_storage = {}


def send_email_otp(user):
    otp = generate_otp()
    user.set_email_otp(otp)
    subject = 'Verify Your Email - Errand App'
    message = f"""
        Hi {user.first_name},

        Your email verification code is: {otp}

        This code will expire in 10 minutes.

        If you didn't request this verification, please ignore this email.

        Best regards,
        The Errand App Team
        """
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

    return otp

def send_sms_otp(user):
    otp = generate_otp()
    user.set_sms_otp(otp)

    print(f"Your Errand App verification code is: {otp} to {user.phone_number} . This code expires in 10 minutes.")

    return otp

def set_verification_tokens(user, email_otp, phone_otp):
    user.email_verification_code = email_otp
    user.phone_verification_code = phone_otp
    user.save()

# def send_verification_email(user, otp):
#     try:
#         subject = 'Verify Your Email - Errand App'
#         message = f"""
#         Hi {user.first_name},
#
#         Your email verification code is: {otp}
#
#         This code will expire in 10 minutes.
#
#         If you didn't request this verification, please ignore this email.
#
#         Best regards,
#         The Errand App Team
#         """
#
#         send_mail(
#             subject=subject,
#             message=message,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[user.email],
#             fail_silently=False,
#         )
#         return True
#     except Exception as e:
#         logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
#         return False
#

# def send_verification_sms(user, otp):
#     try:
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#
#         message = f"Your Errand App verification code is: {otp}. This code expires in 10 minutes."
#
#         client.messages.create(
#             body=message,
#             from_=settings.TWILIO_PHONE_NUMBER,
#             to=str(user.phone_number)
#         )
#         return True
#     except Exception as e:
#         logger.error(f"Failed to send verification SMS to {user.phone_number}: {str(e)}")
#         return False
#


def is_token_expired(token_expires):
    if not token_expires:
        return True
    return timezone.now() > token_expires
