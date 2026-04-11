"""
Celery workers for JobBot background tasks.
Handles scraping, notifications, and heavy processing asynchronously.
"""

import os
from celery import Celery
from kombu import Queue

# Broker configuration - use Redis if available, otherwise RabbitMQ
BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Result backend
RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Create Celery app
app = Celery('jobbot', broker=BROKER_URL, backend=RESULT_BACKEND)

# Configure queues
app.conf.task_queues = (
    Queue('default', routing_key='task.#'),
    Queue('scraping', routing_key='scraping.#'),
    Queue('notifications', routing_key='notifications.#'),
    Queue('ai_processing', routing_key='ai.#'),
)

# Default queue
default_queue = 'default'

# Task routing
task_routes = {
    'workers.tasks.scrape_jobs_for_user': {'queue': 'scraping', 'routing_key': 'scraping.user'},
    'workers.tasks.send_alert_batch': {'queue': 'notifications', 'routing_key': 'notifications.batch'},
    'workers.tasks.process_cv_analysis': {'queue': 'ai_processing', 'routing_key': 'ai.cv'},
    'workers.tasks.generate_cover_letter': {'queue': 'ai_processing', 'routing_key': 'ai.cover'},
}

# Serialization
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'

# Task settings
app.conf.task_track_started = True
app.conf.task_time_limit = 600  # 10 minutes max per task
app.conf.task_soft_time_limit = 300  # Soft limit at 5 minutes
app.conf.worker_prefetch_multiplier = 1  # Fair task distribution
app.conf.worker_concurrency = 4  # Adjust based on CPU cores

# Result expiration
app.conf.result_expires = 3600  # Results expire after 1 hour

# Retry settings
app.conf.task_default_retry_delay = 60  # 1 minute between retries
app.conf.task_max_retries = 3

# Beat scheduler (for periodic tasks)
app.conf.beat_schedule = {
    'cleanup-old-jobs': {
        'task': 'workers.tasks.cleanup_old_jobs',
        'schedule': 3600.0,  # Every hour
    },
}

# Import tasks
app.autodiscover_tasks(['workers'])
