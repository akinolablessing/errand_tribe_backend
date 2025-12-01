from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, filters, permissions
from .models import Task, Escrow, ErrandImage, PickupDelivery, CareTask, VerificationTask, UserProfile, Errand, \
    ErrandApplication, Review

from .serializers import TaskSerializer, SupermarketRunSerializer, PickupDeliverySerializer, ErrandImageSerializer, \
    CareTaskSerializer, VerificationTaskSerializer, UserTierSerializer, ErrandSerializer, TaskWithRunnerSerializer, \
    ErrandApplicationSerializer, ReviewSerializer, RunnerDetailsSerializer


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
            "If they already have tasks, it returns only the most recent task as a flat object."
        ),
        responses={
            200: openapi.Response(
                description="Journey started or latest task returned",
                examples={
                    "application/json": {
                        "success": True,
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
                    "action": "Click 'Post a Task' to create your first one."
                },
                status=status.HTTP_200_OK
            )

        latest_task = TaskSerializer(user_tasks.first()).data

        return Response(
            {
                "success": True,
                "message": "You already have posted tasks.",
                "task": latest_task
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


class VerificationTaskCreateView(generics.CreateAPIView):

    queryset = VerificationTask.objects.all()
    serializer_class = VerificationTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Create a Verification Task",
        operation_description=(
            "Creates a new verification task such as address or document verification.\n\n"
            "Steps covered:\n"
            "- Title & Date\n"
            "- Verification Type\n"
            "- Location\n"
            "- Details (instructions, runner actions, contact info)\n"
            "- Price range"
        ),
        request_body=VerificationTaskSerializer,
        responses={
            201: openapi.Response('Created', VerificationTaskSerializer),
            400: 'Bad Request',
            401: 'Unauthorized'
        }
    )
    def post(self, request, *args, **kwargs):

        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserTierView(generics.RetrieveAPIView):
    serializer_class = UserTierSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get user tier and progress",
        operation_description=(
            "Returns the user's current tier, completed errands count, "
            "and how many more errands are needed to move to Tier 2."
        ),
        responses={200: UserTierSerializer}
    )
    def get(self, request, *args, **kwargs):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.update_tier()
        serializer = self.get_serializer(profile)
        return self.response_ok(serializer.data)

    def response_ok(self, data):
        from rest_framework.response import Response
        return Response(data)

class PostedErrandsView(generics.ListCreateAPIView):
    serializer_class = ErrandSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price_min', 'price_max', 'created_at']


    def get_serializer_context(self):
        return {
            "request": self.request
        }

    def get_queryset(self):
        user = self.request.user
        queryset = Errand.objects.filter(user=user)

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


    @swagger_auto_schema(
        operation_summary="List or Create Tasker’s Posted Errands",
        operation_description=(
            "GET: Retrieve errands posted by the logged-in tasker.\n"
            "POST: Create a new errand for the logged-in user."
        ),
        manual_parameters=[
            openapi.Parameter(
                'category', openapi.IN_QUERY,
                description="Filter errands by category ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'ordering', openapi.IN_QUERY,
                description="Order by price_min, price_max, or created_at",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Search errands by title, description, or location",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: ErrandSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new Errand",
        request_body=ErrandSerializer,
        responses={201: ErrandSerializer}
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ErrandDetailView(generics.RetrieveAPIView):
    queryset = Errand.objects.all()
    serializer_class = ErrandSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(
        operation_summary="Retrieve Full Errand Details",
        operation_description=(
            "Get the complete details of a specific errand by its ID. "
            "Only accessible to authenticated users."
        ),
        responses={200: ErrandSerializer()}
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)




class RecommendedTasksView(generics.ListAPIView):
    serializer_class = ErrandSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price_min', 'price_max', 'created_at']


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(
        operation_summary="Get recommended errands",
        operation_description=(
            "Retrieve errands that are currently open or available for runners.\n"
            "You can filter by category, search by title/description/location, "
            "and sort by recent or price range."
        ),
        manual_parameters=[
            openapi.Parameter(
                'search', openapi.IN_QUERY,
                description="Search errands by title, description, or location",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'sort', openapi.IN_QUERY,
                description="Sort by recent, high_price, or low_price",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'category', openapi.IN_QUERY,
                description="Filter errands by category ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'location', openapi.IN_QUERY,
                description="Filter errands by location",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: ErrandSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Errand.objects.exclude(user=self.request.user).order_by("-created_at")

        search = self.request.query_params.get("search")
        sort = self.request.query_params.get("sort")
        category = self.request.query_params.get("category")
        location = self.request.query_params.get("location")

        if category:
            queryset = queryset.filter(category__id=category)

        if location:
            queryset = queryset.filter(location__icontains=location)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        if sort == "recent":
            queryset = queryset.order_by("-created_at")
        elif sort == "high_price":
            queryset = queryset.order_by("-price_max")
        elif sort == "low_price":
            queryset = queryset.order_by("price_min")

        return queryset

class AvailableTasksView(generics.ListAPIView):
    serializer_class = ErrandSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @swagger_auto_schema(
        operation_summary="List Available Errands",
        operation_description="Retrieve all available errands (open errands not created by the logged-in user).",
        manual_parameters=[
            openapi.Parameter(
                'category', openapi.IN_QUERY,
                description="Filter errands by category ID",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'location', openapi.IN_QUERY,
                description="Filter errands by location name (case-insensitive)",
                type=openapi.TYPE_STRING
            ),
        ],
        responses={200: ErrandSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user

        queryset = (
            Errand.objects
            .exclude(user=user)
            .order_by('-created_at')
        )

        category_id = self.request.query_params.get('category')
        location = self.request.query_params.get('location')

        if category_id:
            queryset = queryset.filter(category__id=category_id)

        if location:
            queryset = queryset.filter(location__icontains=location)

        return queryset

class ApplyErrandView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ErrandApplicationSerializer

    @swagger_auto_schema(operation_summary="Apply to an Errand")
    def post(self, request, errand_id):
        errand = get_object_or_404(Errand, id=errand_id)

        if errand.user == request.user:
            return Response(
                {"detail": "You cannot apply to your own errand."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if ErrandApplication.objects.filter(errand=errand, runner=request.user).exists():
            return Response(
                {"detail": "You have already applied for this errand."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save(
            runner=request.user,
            errand=errand
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ErrandApplicationsListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ErrandApplicationSerializer

    @swagger_auto_schema(operation_summary="List Applications for an Errand")
    def get_queryset(self):
        errand_id = self.kwargs['errand_id']
        return ErrandApplication.objects.filter(errand_id=errand_id)


class UpdateApplicationStatusView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ErrandApplicationSerializer
    lookup_url_kwarg = "application_id"

    @swagger_auto_schema(operation_summary="Accept or Reject an Application")
    def patch(self, request, *args, **kwargs):
        application = self.get_object()
        status_value = request.data.get("status")
        if status_value not in ["accepted", "rejected"]:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        application.status = status_value
        application.save()
        return Response({"detail": f"Application {status_value} successfully."})

class ReviewRunnerView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Review a runner for a completed application",
        operation_description=(
            "Allows the tasker to submit a review for a runner who completed an errand.\n"
            "The review can only be submitted once per completed application."
        ),
        manual_parameters=[
            openapi.Parameter(
                name='application_id',
                in_=openapi.IN_PATH,
                description='ID of the ErrandApplication to review',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=ReviewSerializer,
        responses={
            201: openapi.Response(
                description="Review created successfully",
                schema=ReviewSerializer()
            ),
            400: "Invalid request or application not completed",
            403: "Unauthorized to review this runner",
            404: "Application not found"
        }
    )
    def post(self, request, application_id):
        application = get_object_or_404(ErrandApplication, id=application_id)

        if application.errand.user != request.user:
            return Response(
                {"detail": "You cannot review this application."},
                status=status.HTTP_403_FORBIDDEN
            )

        if application.status != "completed":
            return Response(
                {"detail": "You can only review completed tasks."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if hasattr(application, "review"):
            return Response(
                {"detail": "You have already reviewed this runner."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(errand=application, reviewer=request.user)

        profile = application.runner.profile
        all_reviews = Review.objects.filter(errand__runner=application.runner)
        total = sum(r.rating for r in all_reviews)
        count = all_reviews.count()
        profile.rating = total / count
        profile.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AppliedRunnerDetailsView(generics.RetrieveAPIView):
    serializer_class = RunnerDetailsSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "application_id"

    @swagger_auto_schema(
        operation_summary="Get details of an applied runner",
        operation_description=(
            "Retrieve the full profile of a runner who applied to an errand. "
            "Only accessible to the tasker who posted the errand."
        ),
        manual_parameters=[
            openapi.Parameter(
                name='application_id',
                in_=openapi.IN_PATH,
                description='ID of the ErrandApplication',
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Applied runner details",
                schema=RunnerDetailsSerializer()
            ),
            403: "Permission denied",
            404: "Application not found"
        }
    )
    def get_object(self):
        application_id = self.kwargs.get(self.lookup_url_kwarg)
        application = get_object_or_404(ErrandApplication, id=application_id)

        if application.errand.user != self.request.user:
            raise PermissionDenied("You do not have access to this runner's details.")

        return application

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context