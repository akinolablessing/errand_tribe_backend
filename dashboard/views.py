from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Task, Escrow, ErrandImage, PickupDelivery, CareTask

from .serializers import TaskSerializer, SupermarketRunSerializer, PickupDeliverySerializer, ErrandImageSerializer, \
    CareTaskSerializer


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


class StartTaskJourneyView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Start your first task journey",
        operation_description=(
            "This endpoint initializes the user's task journey. "
            "If the user has not posted any task yet, it prompts them to post their first task. "
            "If they already have tasks, it returns a summary of their most recent ones."
        ),
        responses={
            200: openapi.Response(
                description="Journey started or existing tasks returned",
                examples={
                    "application/json": {
                        "message": "Welcome! You have not posted any task yet.",
                        "action": "Click 'Post a Task' to create your first one."
                    }
                },
            ),
            401: "Unauthorized",
        },
        tags=["Tasks"],
    )
    def get(self, request):
        user = request.user
        user_tasks = Task.objects.filter(poster=user).order_by("-created_at")

        if not user_tasks.exists():
            return Response(
                {
                    "success": True,
                    "message": "Welcome! You have not posted any task yet.",
                    "action": "Click 'Post a Task' to create your first one.",
                },
                status=status.HTTP_200_OK,
            )

        serializer = TaskSerializer(user_tasks, many=True)
        return Response(
            {
                "success": True,
                "message": "You already have posted tasks.",
                "tasks": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class PickupDeliveryCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create a new pickup & delivery errand task.",
        request_body=PickupDeliverySerializer,
        responses={
            201: openapi.Response(
                description="Pickup & delivery task created successfully",
                examples={
                    "application/json": {
                        "message": "Pickup & delivery task created successfully",
                        "data": {
                            "id": "4fbe33f1-b9cb-4c7d-9914-4a2b31e86f8a",
                            "title": "Pick up package from Shoprite",
                            "pickup_location": "Shoprite Ikeja Mall, Lagos",
                            "dropoff_location": "12 Adeola Odeku Street, Victoria Island, Lagos",
                            "is_fragile": True,
                            "requires_signature": True,
                            "price_min": "15000.00",
                            "price_max": "30000.00",
                            "status": "pending"
                        }
                    }
                },
            ),
            400: "Validation Error",
            401: "Unauthorized"
        },
        tags=["Pickup & Delivery"],
    )
    def post(self, request):
        serializer = PickupDeliverySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"message": "Pickup & delivery task created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ErrandImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Upload an image for a PickupDelivery errand (form-data only).",
        manual_parameters=[
            openapi.Parameter(
                name="image",
                in_=openapi.IN_FORM,
                description="Image file to upload (JPEG, PNG, WEBP, etc.)",
                type=openapi.TYPE_FILE,
                required=True,
            ),
            openapi.Parameter(
                name="errand_id",
                in_=openapi.IN_FORM,
                description="Optional: ID of the PickupDelivery to attach the image to",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={
            201: openapi.Response(
                description="Image uploaded successfully",
                examples={
                    "application/json": {
                        "message": "Image uploaded successfully",
                        "data": {
                            "id": "c2f7451a-928d-4e3b-b7e9-96b239c109f5",
                            "image_url": "http://localhost:8000/media/uploads/errand_images/sample.jpg",
                            "errand_id": "8ac5e019-bf11-4b52-a7e2-2a23e83b4e63"
                        }
                    }
                },
            ),
            400: "Validation Error",
            401: "Unauthorized",
        },
        tags=["Pickup & Delivery"],
    )
    def post(self, request):
        image_file = request.FILES.get("image")
        errand_id = request.POST.get("errand_id")

        if not image_file:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        errand = None
        if errand_id:
            try:
                errand = PickupDelivery.objects.get(id=errand_id)
            except PickupDelivery.DoesNotExist:
                return Response(
                    {"error": f"PickupDelivery with id {errand_id} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        errand_image = ErrandImage.objects.create(image=image_file, errand=errand)
        serializer = ErrandImageSerializer(errand_image, context={"request": request})

        return Response(
            {"message": "Image uploaded successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

class CareTaskCreateView(generics.CreateAPIView):

    queryset = CareTask.objects.all()
    serializer_class = CareTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a care task",
        operation_description=(
            "Allows an authenticated user to create a new care task. "
            "The logged-in user will automatically be assigned as the creator of the task."
        ),
        request_body=CareTaskSerializer,
        responses={
            201: openapi.Response(
                description="Care task created successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Care task created successfully",
                        "data": {
                            "id": "a3f1c9a2-7d49-4b1d-bac2-b45b6c17d25f",
                            "title": "Take care of elderly person",
                            "description": "Assist with daily routines and medication",
                            "price": "5000.00",
                            "status": "open",
                            "created_at": "2025-10-29T10:30:00Z",
                            "updated_at": "2025-10-29T10:30:00Z"
                        }
                    }
                },
            ),
            400: "Validation Error",
            401: "Unauthorized",
        },
        tags=["Care Tasks"],
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "success": True,
                "message": "Care task created successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


