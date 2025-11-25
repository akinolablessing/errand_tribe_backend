from django.utils import timezone


from rest_framework import serializers
from .models import Task, SupermarketRun, PickupDelivery, ErrandImage, CareTask, VerificationTask, UserProfile, \
    Category, Errand, ErrandApplication, Review


class TaskSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "category", "category_display",
            "location", "price", "status", "created_at", "updated_at"
        ]
        read_only_fields = ["status", "created_at", "updated_at"]

class SupermarketRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupermarketRun
        fields = '__all__'

class PickupDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = PickupDelivery
        fields = "__all__"
        read_only_fields = ["user", "status", "created_at"]

class ErrandImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    errand_id = serializers.SerializerMethodField()

    class Meta:
        model = ErrandImage
        fields = ["id", "errand_id", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_errand_id(self, obj):
        return str(obj.errand.id) if obj.errand else None

class CareTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareTask
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class VerificationTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationTask
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class UserTierSerializer(serializers.ModelSerializer):
    errands_left_for_next_tier = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['tier', 'errands_completed', 'errands_left_for_next_tier']

    def get_errands_left_for_next_tier(self, obj):
        return max(0, 3 - obj.errands_completed)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

# class ErrandSerializer(serializers.ModelSerializer):
#     category = CategorySerializer()
#
#     class Meta:
#         model = Errand
#         fields = '__all__'
#         read_only_fields = ['user', 'created_at']

class ErrandSerializer(serializers.ModelSerializer):
    client = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)

    applications_count = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()

    class Meta:
        model = Errand
        fields = [
            "id",
            "title",
            "description",
            "location",
            "estimated_duration",
            "price_min",
            "price_max",
            "price_range",
            "deadline",
            "client",
            "category_name",
            "is_overdue",
            "created_at",

            "applications_count",
            "applications",
            "has_applied",
        ]

    def get_client(self, obj):
        user = obj.user
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name if full_name else user.email

    def get_price_range(self, obj):
        return f"₦{float(obj.price_min):,.2f} - ₦{float(obj.price_max):,.2f}"

    def get_is_overdue(self, obj):
        if not obj.deadline:
            return False
        return timezone.now() > obj.deadline


    def get_applications_count(self, obj):
        return obj.applications.count()

    def get_applications(self, obj):
        request = self.context.get("request")
        queryset = obj.applications.all()
        return ErrandApplicationSerializer(queryset, many=True, context={"request": request}).data

    def get_has_applied(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return obj.applications.filter(runner=request.user).exists()


class RunnerProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    errands_left_for_next_tier = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'user_name',
            'tier',
            'errands_completed',
            'errands_left_for_next_tier',
            'latitude',
            'longitude',
            'rating',
        ]

    def get_errands_left_for_next_tier(self, obj):
        return max(0, 3 - obj.errands_completed)

class TaskWithRunnerSerializer(TaskSerializer):
    runner_profile = RunnerProfileSerializer(source='assigned_runner.profile', read_only=True)

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['runner_profile']


class ErrandApplicationSerializer(serializers.ModelSerializer):
    runner_name = serializers.CharField(source="runner.username", read_only=True)
    errand_title = serializers.CharField(source="errand.title", read_only=True)

    class Meta:
        model = ErrandApplication
        fields = [
            "id",
            "errand",
            "errand_title",
            "runner",
            "runner_name",
            "offer_amount",
            "message",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at", "runner_name", "errand_title"]

class ReviewSerializer(serializers.ModelSerializer):
    runner_name = serializers.CharField(source="errand.runner.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "rating", "comment", "runner_name", "created_at"]

from rest_framework import serializers

class RunnerProfileMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "full_name",
            "tier",
            "rating",
            "latitude",
            "longitude",
            "errands_completed",
        ]

    def get_full_name(self, obj):
        user = obj.user
        name = f"{user.first_name} {user.last_name}".strip()
        return name if name else user.username


class RunnerDetailsSerializer(serializers.ModelSerializer):
    runner_profile = serializers.SerializerMethodField()
    errand_title = serializers.CharField(source="errand.title", read_only=True)

    class Meta:
        model = ErrandApplication
        fields = [
            "id",
            "errand_title",
            "offer_amount",
            "message",
            "status",
            "created_at",
            "runner_profile",
        ]

    def get_runner_profile(self, obj):
        profile = obj.runner.profile
        return RunnerProfileMiniSerializer(profile).data
