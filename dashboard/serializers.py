from rest_framework import serializers
from .models import Task, SupermarketRun


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