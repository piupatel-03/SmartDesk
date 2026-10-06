import logging
import time
import uuid

from django.conf import settings
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)


class RequestTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Reuse incoming request ID or create a new one
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.request_id = request_id

        # Maintenance mode
        if getattr(settings, "MAINTENANCE_MODE", False):

            # Health endpoint must always work
            is_health = request.path == "/api/health/"

            # Check if user is a Manager from JWT
            is_manager = False

            auth_header = request.headers.get("Authorization", "")

            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]

                try:
                    access_token = AccessToken(token)
                    user_id = access_token["user_id"]

                    user = User.objects.get(id=user_id)
                    is_manager = user.groups.filter(
                        name="Manager"
                    ).exists()

                except Exception:
                    is_manager = False

            if not is_health and not is_manager:
                response = JsonResponse(
                    {
                        "detail": "Service is temporarily under maintenance."
                    },
                    status=503
                )

                response["X-Request-ID"] = request_id
                return response

        response = self.get_response(request)

        duration = (time.time() - start_time) * 1000

        response["X-Request-ID"] = request_id
        response["X-Response-Time-ms"] = f"{duration:.2f}"

        user = getattr(request, "user", None)

        if user and user.is_authenticated:
            username = user.username
        else:
            username = "anonymous"

        logger.info(
            "timestamp=%s request_id=%s method=%s path=%s "
            "user=%s status=%s duration=%.2fms",
            time.strftime("%Y-%m-%d %H:%M:%S"),
            request_id,
            request.method,
            request.path,
            username,
            response.status_code,
            duration,
        )

        return response