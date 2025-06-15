# apps/notifications/apps.py
from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration de l'application Notifications."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications OPRAG'
    
    def ready(self):
        """Initialisation des signaux et tâches périodiques."""
        try:
            import apps.notifications.signals  # noqa
            self._setup_periodic_tasks()
        except ImportError:
            pass
    
    def _setup_periodic_tasks(self):
        """Configure les tâches périodiques de notification."""
        from django_celery_beat.models import PeriodicTask, CrontabSchedule
        import json
        
        # Vérification quotidienne des alertes à 8h
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=0,
            hour=8,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )
        
        PeriodicTask.objects.get_or_create(
            crontab=schedule,
            name='Vérification alertes quotidiennes OPRAG',
            task='apps.notifications.tasks.check_daily_alerts',
            kwargs=json.dumps({}),
        )