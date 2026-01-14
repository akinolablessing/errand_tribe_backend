# metrics_calculator.py
from django.db.models import Count, Avg, Sum
from .models import Task, TaskCategory, TaskStatistic

class TimeSavedMetric:
    """Calculate time saved metrics"""
    
    @staticmethod
    def calculate(user):
        completed_tasks = user.posted_tasks.filter(status=Task.Status.COMPLETED)
        
        estimated_time_saved = completed_tasks.count() * 2  # hours
        actual_time_saved = TimeSavedMetric._calculate_actual_time_saved(completed_tasks)
        
        return {
            'actual': actual_time_saved,
            'estimated': estimated_time_saved
        }
    
    @staticmethod
    def _calculate_actual_time_saved(completed_tasks):
        time_saved = 0
        for task in completed_tasks:
            time_weights = {
                TaskCategory.SUPERMARKET_RUNS: 2.5,
                TaskCategory.PICKUP_DELIVERY: 1.5,
                TaskCategory.LOCAL_MICRO: 1.0,
                TaskCategory.CARE_TASKS: 3.0,
                TaskCategory.VERIFY_IT: 2.0
            }
            time_saved += time_weights.get(task.category, 1.5)
        return time_saved

class RepeatedRunnersMetric:
    """Calculate repeated runners metric"""
    
    @staticmethod
    def calculate(user):
        repeated_runners = user.posted_tasks.filter(
            worker__isnull=False
        ).values('worker').annotate(
            count=Count('worker')
        ).filter(count__gt=1).count()
        return repeated_runners

class TotalSpentMetric:
    """Calculate total spending metrics"""
    
    @staticmethod
    def calculate(user):
        tasks = user.posted_tasks.all()
        completed_tasks = tasks.filter(status=Task.Status.COMPLETED)
        
        total_spent = completed_tasks.aggregate(total=Sum('price'))['total'] or 0
        estimated_spending = TotalSpentMetric._estimate_spending(tasks)
        
        return {
            'actual': float(total_spent),
            'estimated': estimated_spending
        }
    
    @staticmethod
    def _estimate_spending(tasks):
        avg_price = tasks.aggregate(avg=Avg('price'))['avg'] or 0
        total_tasks = tasks.count()
        return float(avg_price * total_tasks * 0.8)

class SuccessRateMetric:
    """Calculate success rate metrics with categorization"""
    
    @staticmethod
    def calculate(user):
        # Use TaskStatistic if available, otherwise calculate directly
        try:
            stats = user.task_stats
            actual_rate = float(stats.success_rate)
        except TaskStatistic.DoesNotExist:
            tasks = user.posted_tasks.all()
            actual_rate = SuccessRateMetric._calculate_success_rate(tasks)
        
        estimated_success_rate = 85.0  # Industry average
        
        # Categorize the success rate
        rating = SuccessRateMetric._categorize_success_rate(actual_rate)
        
        return {
            'actual': actual_rate,
            'estimated': estimated_success_rate,
            'rating': rating,
            'message': SuccessRateMetric._get_rating_message(rating)
        }
    
    @staticmethod
    def _calculate_success_rate(tasks):
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status=Task.Status.COMPLETED).count()
        return (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    @staticmethod
    def _categorize_success_rate(rate):
        """Categorize success rate into different levels"""
        if rate >= 0 and rate <= 40:
            return "not_good"
        elif rate > 40 and rate <= 60:
            return "average"
        elif rate > 60 and rate <= 80:
            return "good"
        elif rate > 80 and rate <= 100:
            return "excellent"
        else:
            return "unknown"
    
    @staticmethod
    def _get_rating_message(rating):
        """Get descriptive message for each rating"""
        messages = {
            "not_good": "Needs improvement - try hiring more reliable runners",
            "average": "Okay - consider building relationships with trusted runners",
            "good": "Good - you're getting consistent results",
            "excellent": "Excellent - you've mastered task delegation!",
            "unknown": "Not enough data to rate"
        }
        return messages.get(rating, "Not enough data to rate")

class CommonErrandMetric:
    """Calculate common errand metric"""
    
    @staticmethod
    def calculate(user):
        tasks = user.posted_tasks.all()
        
        if tasks.count() == 0:
            return "No errands yet"
        
        common_category = tasks.values('category').annotate(
            count=Count('category')
        ).order_by('-count').first()
        
        if common_category:
            return dict(TaskCategory.choices).get(common_category['category'], "Unknown")
        return "No errands yet"

class AvgCostPerErrandMetric:
    """Calculate average cost per errand metrics"""
    
    @staticmethod
    def calculate(user):
        # Use TaskStatistic if available, otherwise calculate directly
        try:
            stats = user.task_stats
            actual_avg = float(stats.average_cost_per_errand)
        except TaskStatistic.DoesNotExist:
            completed_tasks = user.posted_tasks.filter(status=Task.Status.COMPLETED)
            actual_avg = AvgCostPerErrandMetric._calculate_avg_cost(completed_tasks)
        
        tasks = user.posted_tasks.all()
        estimated_avg_cost = AvgCostPerErrandMetric._estimate_avg_cost(tasks)
        
        return {
            'actual': actual_avg,
            'estimated': estimated_avg_cost
        }
    
    @staticmethod
    def _calculate_avg_cost(completed_tasks):
        if completed_tasks.count() == 0:
            return 0
        avg = completed_tasks.aggregate(avg=Avg('price'))['avg'] or 0
        return float(avg)
    
    @staticmethod
    def _estimate_avg_cost(tasks):
        if tasks.count() == 0:
            return 0
        avg = tasks.aggregate(avg=Avg('price'))['avg'] or 0
        return float(avg)


class PerformanceMetricsCalculator:
    """Main calculator that orchestrates all metric classes"""
    
    @staticmethod
    def calculate_metrics(user):
        """Calculate all performance metrics for dashboard"""
        return {
            'time_saved': TimeSavedMetric.calculate(user),
            'repeated_runners': RepeatedRunnersMetric.calculate(user),
            'total_spent': TotalSpentMetric.calculate(user),
            'success_rate': SuccessRateMetric.calculate(user),
            'common_errand': CommonErrandMetric.calculate(user),
            'avg_cost_per_errand': AvgCostPerErrandMetric.calculate(user),
        }