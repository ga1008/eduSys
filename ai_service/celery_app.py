from celery import Celery
from kombu import Queue, Exchange  # For more advanced routing if needed
from app.core.config import settings

# Ensure ARK_API_KEY is set for VolcEngine provider if it's used within Celery tasks
# This might be redundant if tasks.py imports from llm_router which initializes providers
import os

if settings.VC_API_KEY and not os.getenv("ARK_API_KEY"):
    os.environ["ARK_API_KEY"] = settings.VC_API_KEY

celery_app = Celery(
    'ai_service_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']  # Points to the tasks module
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    worker_concurrency=10,  # Default 10 concurrent tasks per worker, adjust as needed
    worker_prefetch_multiplier=1,  # To ensure fair task distribution for long tasks
    task_acks_late=True,  # Acknowledge task after it's completed/failed
    task_reject_on_worker_lost=True,  # Requeue task if worker dies
    task_queues=(
        Queue('ai_default_queue', Exchange('ai_default_exchange'), routing_key='ai.default'),
        Queue('ai_long_running_queue', Exchange('ai_long_running_exchange'), routing_key='ai.long_running'),
    ),
    task_default_queue='ai_default_queue',
    task_default_exchange='ai_default_exchange',
    task_default_routing_key='ai.default',
)

# Optional: Define routes for specific tasks if needed later
# celery_app.conf.task_routes = {
# 'app.tasks.generate_ai_response_async': {'queue': 'ai_long_running_queue'},
# }

if __name__ == '__main__':
    celery_app.start()
