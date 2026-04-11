# Workers module for Celery background tasks
# Import tasks to register them with Celery
from .tasks import (
    scrape_jobs_for_user,
    send_alert_batch,
    process_cv_analysis,
    generate_cover_letter,
    cleanup_old_jobs,
    schedule_user_alerts,
)

__all__ = [
    'scrape_jobs_for_user',
    'send_alert_batch',
    'process_cv_analysis',
    'generate_cover_letter',
    'cleanup_old_jobs',
    'schedule_user_alerts',
]
