from django.urls import path
from .views import CreateTaskView

urlpatterns = [
    path("tasks/create/", CreateTaskView.as_view(), name="create-task"),
]
