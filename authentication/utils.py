from datetime import timedelta

from django.utils import timezone
from twilio.rest import Client
import logging
import random
from django.core.mail import send_mail
from django.conf import settings
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import random

logger = logging.getLogger(__name__)



def generate_otp():
    return str(random.randint(100000, 999999))



otp_storage = {}


def send_email_otp(user):
    """
        Generate OTP and send it to the user's email using Brevo.
        """
    # Generate a 6-digit OTP
    otp = str(random.randint(100000, 999999))

    user.set_email_otp(otp)
    # Configure Brevo
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Prepare email
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": user.email, "name": user.first_name}],
        sender={"email": "ettribe.errands@gmail.com", "name": "Errand Tribe"},
        subject="Your OTP Code",
        html_content=f"""
                <p>Hi {user.first_name},</p>
                <p>Your OTP code is: <b>{otp}</b></p>
                <p>It will expire in 30 minutes.</p>
            """,
    )

    try:
        api_instance.send_transac_email(send_smtp_email)
        return otp
    except ApiException as e:
        raise Exception(f"Failed to send OTP: {e}")


# def verify_email_otp(self, otp: str, expiry_seconds: int = 600) -> bool:
#     if not self.email_otp or self.email_otp != str(otp):
#         return False
#
#     if self.email_otp_created_at < timezone.now() - timedelta(minutes=30):
#         return False
#     self.is_email_verified = True
#     self.email_otp = None
#     self.save(update_fields=["is_email_verified", "email_otp"])
#     return True


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
