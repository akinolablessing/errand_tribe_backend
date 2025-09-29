import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ErrandTribe.settings")
django.setup()

from django.core.mail import send_mail

result = send_mail(
    "Test Email",
    "Hello from Django",
    "ettribe.errands@gmail.com",      # must match EMAIL_HOST_USER
    ["winnermhidey@gmail.com"],  # replace with your real email
    fail_silently=False,
)

print("✅ Emails sent:", result)
