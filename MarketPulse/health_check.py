from django.http import JsonResponse
from django.db import connection
from django.conf import settings

try:
    import redis
except Exception:
    redis = None


def health(request):
    """Lightweight health endpoint for load balancers and orchestrators.

    Returns 200 when the app is responsive. Includes best-effort checks for
    database and Redis broker; if either check fails, returns 503.
    """
    payload = {
        "status": "healthy",
        "message": "MarketPulse is running",
    }

    http_status = 200

    # Database check (best effort)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        payload["database"] = "ok"
    except Exception:
        payload["database"] = "error"
        payload["status"] = "degraded"
        http_status = 503

    # Redis/Broker check (best effort)
    try:
        if redis is not None:
            broker_url = getattr(
                settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"
            )
            client = redis.Redis.from_url(
                broker_url, socket_connect_timeout=1, socket_timeout=1
            )
            client.ping()
            payload["redis"] = "ok"
        else:
            payload["redis"] = "unavailable"
    except Exception:
        payload["redis"] = "error"
        payload["status"] = "degraded"
        http_status = 503

    return JsonResponse(payload, status=http_status)
