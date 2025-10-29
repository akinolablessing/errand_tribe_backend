from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL



class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=5, default="NGN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.balance} {self.currency}"

    def credit(self, amount, description="Wallet funded"):

        self.balance += amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.TransactionType.CREDIT,
            description=description,
        )

    def debit(self, amount, description="Wallet debited"):

        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()
        Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.TransactionType.DEBIT,
            description=description,
        )


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user} - {self.transaction_type} - {self.amount}"



class TaskCategory(models.TextChoices):
    LOCAL_MICRO = "local_micro", "Local Micro Task"
    SUPERMARKET_RUNS = "supermarket_runs", "Supermarket Runs"
    PICKUP_DELIVERY = "pickup_delivery", "Pickup & Delivery"
    CARE_TASKS = "care_tasks", "Care Tasks"
    VERIFY_IT = "verify_it", "Verify It"


class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    poster = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_tasks")
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_tasks")

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=TaskCategory.choices)
    location = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def assign_worker(self, worker):

        self.worker = worker
        self.status = self.Status.ASSIGNED
        self.save()

    def mark_completed(self):

        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.title} - {self.get_category_display()}"



class TaskApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_applications")
    message = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("task", "applicant")

    def __str__(self):
        return f"{self.applicant} → {self.task.title}"


class Escrow(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        HELD = "held", "Held in Escrow"
        RELEASED = "released", "Released to Worker"
        REFUNDED = "refunded", "Refunded to Poster"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name="escrow")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def hold_funds(self):
        self.status = self.Status.HELD
        self.save()

    def release_funds(self):
        self.status = self.Status.RELEASED
        self.released_at = timezone.now()
        self.save()

    def refund(self):
        self.status = self.Status.REFUNDED
        self.save()

    def __str__(self):
        return f"Escrow for {self.task.title} - {self.status}"



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


class SupermarketRun(models.Model):
    title = models.CharField(max_length=255)
    needed_by_date = models.DateField()
    needed_by_time = models.TimeField()

    location = models.CharField(max_length=255)

    shopping_list = models.JSONField(
        help_text="List of items with optional properties like perishable or substitutions")
    list_image = models.ImageField(upload_to='shopping_lists/', null=True, blank=True)

    drop_off_location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PickupDelivery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    is_urgent = models.BooleanField(default=False)
    deadline = models.DateTimeField(null=True, blank=True)

    pickup_location = models.CharField(max_length=255)
    pickup_lat = models.FloatField(null=True, blank=True)
    pickup_lng = models.FloatField(null=True, blank=True)
    sender_phone = models.CharField(max_length=20)

    dropoff_location = models.CharField(max_length=255)
    dropoff_lat = models.FloatField(null=True, blank=True)
    dropoff_lng = models.FloatField(null=True, blank=True)
    recipient_phone = models.CharField(max_length=20)

    requires_signature = models.BooleanField(default=False)
    is_fragile = models.BooleanField(default=False)
    special_note = models.TextField(blank=True, null=True)
    images = models.JSONField(default=list, blank=True)

    price_min = models.DecimalField(max_digits=10, decimal_places=2)
    price_max = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ErrandImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    errand = models.ForeignKey(
        "PickupDelivery", on_delete=models.CASCADE, null=True, blank=True, related_name="images_set"
    )
    image = models.ImageField(upload_to="uploads/errand_images/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.errand or 'Unassigned'}"