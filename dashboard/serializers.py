from rest_framework import serializers
from .models import Task, SupermarketRun, PickupDelivery, ErrandImage, CareTask, VerificationTask


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