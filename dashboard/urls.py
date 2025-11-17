from django.urls import path
from .views import CreateTaskView, DashboardOverviewAPIView,PerformanceMetricsAPIView,TaskStatisticsAPIView,TimeSavedMetricAPIView, \
RepeatedRunnersMetricAPIView,TotalSpentMetricAPIView,SuccessRateMetricAPIView,CommonErrandMetricAPIView,AvgCostPerErrandMetricAPIView

urlpatterns = [
    path("tasks/create/", CreateTaskView.as_view(), name="create-task"),
    path('overview/', DashboardOverviewAPIView.as_view(), name='dashboard-overview'),
    path('performance-metrics/', PerformanceMetricsAPIView.as_view(), name='performance-metrics'),
    path('statistics/', TaskStatisticsAPIView.as_view(), name='tasker-statistics'),
    
    
    path('metrics/time-saved/', TimeSavedMetricAPIView.as_view(), name='time-saved-metric'),
    path('metrics/repeated-runners/', RepeatedRunnersMetricAPIView.as_view(), name='repeated-runners-metric'),
    path('metrics/total-spent/', TotalSpentMetricAPIView.as_view(), name='total-spent-metric'),
    path('metrics/success-rate/', SuccessRateMetricAPIView.as_view(), name='success-rate-metric'),
    path('metrics/common-errand/', CommonErrandMetricAPIView.as_view(), name='common-errand-metric'),
    path('metrics/avg-cost/', AvgCostPerErrandMetricAPIView.as_view(), name='avg-cost-metric'),

]
