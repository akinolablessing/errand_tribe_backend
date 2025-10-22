from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Task
from .serializers import TaskSerializer, SupermarketRunSerializer


class CreateTaskView(generics.CreateAPIView):

    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a new task",
        operation_description="Allows an authenticated user to create a new task. The poster is automatically set from the logged-in user.",
        request_body=TaskSerializer,
        responses={
            201: openapi.Response(
                description="Task created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Task created successfully",
                        "data": {
                            "id": "uuid",
                            "title": "Buy groceries",
                            "description": "Purchase groceries at Shoprite",
                            "category": "supermarket_runs",
                            "location": "Ikeja, Lagos",
                            "price": "3500.00",
                            "status": "open",
                            "created_at": "2025-10-20T19:30:00Z",
                            "updated_at": "2025-10-20T19:30:00Z"
                        }
                    }
                },
            ),
            400: "Validation Error",
            401: "Unauthorized",
        },
    )
    def create(self, request, *args, **kwargs):
        """Handle POST /api/tasks/create/"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "success": True,
            "message": "Task created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(poster=self.request.user)

class SupermarketRunCreateView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a supermarket run",
        operation_description=(
            "Allows an authenticated user to create a supermarket run task. "
            "This could be for buying items from a specific supermarket."
        ),
        request_body=SupermarketRunSerializer,
        responses={
            201: openapi.Response(
                description="Supermarket run created successfully",
                examples={
                    "application/json": {
                        "message": "Supermarket Run Created",
                        "data": {
                            "id": "uuid",
                            "supermarket_name": "Shoprite",
                            "items": [
                                {"name": "Milk", "quantity": 2},
                                {"name": "Bread", "quantity": 1}
                            ],
                            "pickup_location": "Ikeja City Mall",
                            "dropoff_location": "Yaba, Lagos",
                            "price": "2500.00",
                            "status": "open",
                            "created_at": "2025-10-20T19:45:00Z"
                        }
                    }
                },
            ),
            400: "Validation Error",
            401: "Unauthorized",
        },
    )
    def post(self, request):

        serializer = SupermarketRunSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Supermarket Run Created",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)