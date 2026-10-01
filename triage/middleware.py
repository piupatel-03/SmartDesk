import time
import uuid
import logging
from django.conf import settings

logger = logging.getLogger("smartdesk")

class RequestTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request.request_id = request_id

        if getattr(settings, "MAINTENANCE_MODE", False):
            from django.http import JsonResponse

            return JsonResponse(
                {"detail": "Service is temporarily under maintenance."},
                status=503,
            )

        start_time = time.time()

        response = self.get_response(request)
        duration = (time.time() - start_time) * 1000

        response["X-Request-ID"] = request_id
        response["X-Response-time-ms"] =f"{duration:.2f}"

        logger.info(
            "%s %s | status=%s | request_id=%s | response_time=%.2fms",
            request.method,
            request.path,
            response.status_code,
            request_id,
            duration,
        )
        return response