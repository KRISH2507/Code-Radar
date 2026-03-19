"""
Celery application configuration.
Redis/Celery is OPTIONAL — the API will work without it.
Background tasks simply won't run if Redis is unavailable.
"""

celery_app = None

try:
    from celery import Celery
    from app.core.config import settings

    if settings.REDIS_URL:
        celery_app = Celery(
            "code_radar",
            broker=settings.REDIS_URL,
            backend=settings.REDIS_URL,
        )

        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            broker_connection_retry_on_startup=False,
            broker_connection_retry=False,
            broker_connection_max_retries=1,
            broker_transport_options={'connect_timeout': 3},
        )
        print("[OK] Celery configured with Redis")
    else:
        print("[WARN] Redis URL not configured - background tasks disabled")

except Exception as e:
    print(f"[WARN] Celery/Redis not available: {e} - background tasks disabled")
    celery_app = None
