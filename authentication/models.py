import uuid

from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django.utils import timezone

from ErrandTribe import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(
        max_length=10,
        choices=[("runner", "Runner"), ("tasker", "Tasker")],
        null=True,
        blank=True,
    )

    is_email_verified = models.BooleanField(default=False)
    is_identity_verified = models.BooleanField(default=False)
    has_uploaded_picture = models.BooleanField(default=False)
    has_enabled_location = models.BooleanField(default=False)
    has_withdrawal_method = models.BooleanField(default=False)
    has_funded_wallet = models.BooleanField(default=False)

    profile_picture = models.ImageField(upload_to="profile_pictures/", blank=True, null=True)
    wallet_balance = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)

    LOCATION_CHOICES = [
        ("while_using_app", "While Using App"),
        ("always", "Always"),
    ]
    location_permission = models.CharField(
        max_length=20, choices=LOCATION_CHOICES, default="while_using_app"
    )

    email_otp = models.CharField(max_length=6, null=True, blank=True)
    email_otp_created_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]
    objects = CustomUserManager()

    def set_email_otp(self, otp):
        self.email_otp = otp
        self.email_otp_created_at = timezone.now()
        self.save(update_fields=["email_otp", "email_otp_created_at"])


class CountryChoices(models.TextChoices):
    NIGERIA = "Nigeria", "Nigeria"
    KENYA = "Kenya", "Kenya"
    TOGO = "Togo", "Togo"
    GHANA = "Ghana", "Ghana"

class DocumentTypeChoices(models.TextChoices):
    NATIONAL_ID = "National ID", "National ID"
    DRIVERS_LICENSE = "Driver's License", "Driver's License"
    PASSPORT = "Passport", "Passport"
    REFUGEE_ID = "Alien Card/Carte Nationale d'Identite", "Alien Card/Carte Nationale d'Identite"

class IdentityVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="identity_verification")
    country = models.CharField(max_length=50, choices=CountryChoices.choices)
    document_type = models.CharField(max_length=50, choices=DocumentTypeChoices.choices)
    document_file = models.FileField(upload_to='identity_documents/')
    verified = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.document_type} ({self.country})"



class WithdrawalMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    METHOD_CHOICES = (
        ("bank", "Bank"),
        ("paypal", "PayPal"),
        ("mobile_money", "Mobile Money"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawal_methods")
    method_type = models.CharField(max_length=50, choices=METHOD_CHOICES, default="bank")
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.method_type} - {self.account_name}"