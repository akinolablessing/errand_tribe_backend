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


def send_email_otp(email):
    """Generate and send OTP to email, store in otp_storage."""
    otp = generate_otp()
    otp_storage[email] = otp  # save OTP temporarily

    subject = "Your OTP Code"
    message = f"Your OTP code is {otp}. It will expire in 5 minutes."
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

    return otp

def send_sms_otp(phone_number):
    """Generate and send OTP to phone (stub or via SMS provider)."""
    otp = generate_otp()
    otp_storage[phone_number] = otp  # save OTP temporarily

    # Here you would integrate with your SMS provider
    print(f"Sending SMS OTP {otp} to {phone_number}")

    return otp

def set_verification_tokens(user, email_otp, phone_otp):
    user.email_verification_code = email_otp
    user.phone_verification_code = phone_otp
    user.save()

def send_verification_email(user, otp):
    """Send email verification OTP to user"""
    try:
        subject = 'Verify Your Email - Errand App'
        message = f"""
        Hi {user.first_name},

        Your email verification code is: {otp}

        This code will expire in 10 minutes.

        If you didn't request this verification, please ignore this email.

        Best regards,
        The Errand App Team
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def send_verification_sms(user, otp):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        message = f"Your Errand App verification code is: {otp}. This code expires in 10 minutes."

        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=str(user.phone_number)
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send verification SMS to {user.phone_number}: {str(e)}")
        return False


# def set_verification_tokens(user, email_otp=None, phone_otp=None):
#     """Set verification tokens for user with expiration"""
#     expiry_time = timezone.now() + timedelta(minutes=10)
#
#     if email_otp:
#         user.email_verification_token = email_otp
#         user.email_token_expires = expiry_time
#
#     if phone_otp:
#         user.phone_verification_token = phone_otp
#         user.phone_token_expires = expiry_time
#
#     user.save(update_fields=[
#         'email_verification_token', 'email_token_expires',
#         'phone_verification_token', 'phone_token_expires'
#     ])
#

def is_token_expired(token_expires):
    if not token_expires:
        return True
    return timezone.now() > token_expires
