import uuid
from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models
from django.utils import timezone

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
    email_otp = models.CharField(max_length=6, null=True, blank=True)
    email_otp_created_at = models.DateTimeField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)  # 🔑 required for login

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone_number"]
    objects = CustomUserManager()

    def set_email_otp(self, otp: str):
        self.email_otp = otp
        self.email_otp_created_at = timezone.now()
        self.save()

    def verify_email_otp(self, otp: str, expiry_seconds: int = 600) -> bool:
        if (
            self.email_otp == otp
            and (timezone.now() - self.email_otp_created_at).seconds < expiry_seconds
        ):
            self.is_email_verified = True
            self.email_otp = None
            self.save()
            return True
        return False
