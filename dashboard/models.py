from datetime import timedelta

from django.utils import timezone

from django.db import models
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL


class Wallet(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=5, default="NGN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.balance} {self.currency}"

    def credit(self, amount):

        self.balance += amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.TransactionType.CREDIT,
            description="Wallet funded",
        )

    def debit(self, amount):

        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.TransactionType.DEBIT,
            description="Wallet debited",
        )


class Transaction(models.Model):

    class TransactionType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.email} - {self.transaction_type} - {self.amount}"


class TaskStatistic(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="task_stats")
    total_tasks_posted = models.PositiveIntegerField(default=0)
    total_tasks_completed = models.PositiveIntegerField(default=0)
    respected_runner_count = models.PositiveIntegerField(default=0)
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_time_saved = models.DurationField(default=timedelta())
    average_cost_per_errand = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def update_success_rate(self):
        if self.total_tasks_posted > 0:
            self.success_rate = (self.total_tasks_completed / self.total_tasks_posted) * 100
        else:
            self.success_rate = 0
        self.save()

    def __str__(self):
        return f"Stats for {self.user}"


class Errand(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_errands")
    runner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_errands")
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def mark_completed(self):
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return self.title