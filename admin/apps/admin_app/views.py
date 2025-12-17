from django.shortcuts import render
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from .models import (
    User, Task, CompletedTask, DailyUserTask
)


@staff_member_required
def admin_dashboard(request):
    """Дашборд админки со статистикой"""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Статистика выполненных задач
    completed_today = CompletedTask.objects.filter(
        completed_at__date=today
    ).count()
    
    completed_yesterday = CompletedTask.objects.filter(
        completed_at__date=yesterday
    ).count()
    
    completed_week = CompletedTask.objects.filter(
        completed_at__date__gte=week_ago
    ).count()
    
    completed_month = CompletedTask.objects.filter(
        completed_at__date__gte=month_ago
    ).count()
    
    # Статистика пользователей
    total_users = User.objects.count()
    active_users_today = DailyUserTask.objects.filter(
        date=today
    ).values('user').distinct().count()
    
    # Статистика заданий
    total_tasks = Task.objects.count()
    active_tasks = Task.objects.filter(is_active=True).count()
    
    stats = {
        'completed_today': completed_today,
        'completed_yesterday': completed_yesterday,
        'completed_week': completed_week,
        'completed_month': completed_month,
        'total_users': total_users,
        'active_users_today': active_users_today,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
    }
    
    return render(request, 'admin/dashboard.html', {'stats': stats})
