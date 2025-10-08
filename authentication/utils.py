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

    otp = str(random.randint(100000, 999999))

    user.set_email_otp(otp)
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

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




def send_sms_otp(user):
    otp = generate_otp()
    user.set_sms_otp(otp)

    print(f"Your Errand App verification code is: {otp} to {user.phone_number} . This code expires in 10 minutes.")

    return otp

def set_verification_tokens(user, email_otp, phone_otp):
    user.email_verification_code = email_otp
    user.phone_verification_code = phone_otp
    user.save()



def is_token_expired(token_expires):
    if not token_expires:
        return True
    return timezone.now() > token_expires
