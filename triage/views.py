from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from django.db import connection
from django.conf import settings
import redis
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status
from .permissions import IsManagerOrAgent, IsManager
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics  # import DRF api views
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Customer, Ticket, DailyReport
from django.db.models import Count
from .authentication import CustomTokenObtainPairSerializer
from .serializers import CustomerSerializer, TicketSerializer, DailyReportSerializer
from rest_framework.exceptions import PermissionDenied, ValidationError


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

class PublicTicketThrottle(AnonRateThrottle):
    scope = "anon"


class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    throttle_classes = [PublicTicketThrottle]

    def get_permissions(self):
        if self.request.method == "POST":
            return [AllowAny()]

        return [IsManagerOrAgent()]

    filterset_fields = [
        "status",
        "category",
        "priority",
        "channel",
        "sla_breached",
    ]

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "ticket_id",
        "subject",
        "description",
    ]

    ordering_fields = [
        "created_at",
        "resolved_at",
        "priority",
        "status",
    ]

    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="Manager").exists():
            queryset = Ticket.objects.all()

        elif user.groups.filter(name="Agent").exists():
            queryset = Ticket.objects.filter(assigned_agent=user)

        else:
            return Ticket.objects.none()

        # Assessment requires ?agent=<agent_id>
        agent_id = self.request.query_params.get("agent")

        if agent_id:
            queryset = queryset.filter(assigned_agent_id=agent_id)

        return queryset
    
    def create(self, request, *args, **kwargs):
        from .tasks import process_public_ticket

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = process_public_ticket.delay(
            dict(serializer.validated_data)
        )

        return Response(
            {
                "message": "Ticket submitted successfully.",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    

class CustomLoginView(TokenObtainPairView):    
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_205_RESET_CONTENT
            )

        except Exception:
            return Response(
                {"error": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsManagerOrAgent]

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="Manager").exists():
            return Ticket.objects.all()

        if user.groups.filter(name="Agent").exists():
            return Ticket.objects.filter(assigned_agent=user)

        return Ticket.objects.none()

    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied

        if not self.request.user.groups.filter(name="Manager").exists():
            raise PermissionDenied(
                "Only managers can delete tickets."
            )

        instance.delete()

class TicketAssignView(APIView):
    permission_classes = [IsManagerOrAgent]

    def post(self, request, pk):
        if not request.user.groups.filter(name="Manager").exists():
            raise PermissionDenied("Only managers can assign tickets.")

        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        agent_id = request.data.get("agent_id")

        if not agent_id:
            raise ValidationError(
                {"agent_id": "agent_id is required."}
            )

        try:
            from django.contrib.auth.models import User
            agent = User.objects.get(
                id=agent_id,
                groups__name="Agent",
            )
        except User.DoesNotExist:
            raise ValidationError(
                {"agent_id": "Agent not found."}
            )

        ticket.assigned_agent = agent
        ticket.save(update_fields=["assigned_agent"])

        from .models import TicketEvent
        from .services.notifications import send_ticket_event

        TicketEvent.objects.create(
            ticket=ticket,
            event_type="ASSIGNED",
            description=f"Ticket assigned to {agent.username}.",
        )

        send_ticket_event(
            ticket,
            "ticket.assigned",
            {
                "agent_id": agent.id,
                "agent_username": agent.username,
            },
        )

        return Response({
            "message": "Ticket assigned successfully.",
            "ticket_id": ticket.ticket_id,
            "assigned_agent": agent.username,
        })

class TicketTransitionView(APIView):
    permission_classes = [IsManagerOrAgent]

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response(
                {"detail": "Ticket not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        # Agents can only transition their assigned tickets
        if user.groups.filter(name="Agent").exists():
            if ticket.assigned_agent_id != user.id:
                return Response(
                    {"detail": "You can only update your assigned tickets."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"detail": "status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .services.ticket import update_ticket_status

        try:
            update_ticket_status(ticket, new_status)
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            "message": "Ticket status updated successfully.",
            "ticket_id": ticket.ticket_id,
            "status": ticket.status,
        })
        
class TicketStatsView(APIView):
    queryset = DailyReport.objects.all().order_by("-report_date")
    serializer_class = DailyReportSerializer
    permission_classes = [IsManagerOrAgent]

    def get(self, request):
        user = request.user

        if user.groups.filter(name="Manager").exists():
            tickets = Ticket.objects.all()

        elif user.groups.filter(name="Agent").exists():
            tickets = Ticket.objects.filter(assigned_agent=user)

        else:
            tickets = Ticket.objects.none()

        data = {
            "total_tickets": tickets.count(),
            "open_tickets": tickets.filter(status="Open").count(),
            "in_progress_tickets": tickets.filter(status="In Progress").count(),
            "resolved_tickets": tickets.filter(status="Resolved").count(),
            "closed_tickets": tickets.filter(status="Closed").count(),
            "high_priority": tickets.filter(priority="High").count(),
            "medium_priority": tickets.filter(priority="Medium").count(),
            "low_priority": tickets.filter(priority="Low").count(),
        }

        return Response(data)


class DailyReportListView(generics.ListAPIView):
    queryset = DailyReport.objects.all().order_by("-report_date")
    serializer_class = DailyReportSerializer
    permission_classes = [IsManager]


class DailyReportGenerateView(APIView):
    permission_classes = [IsManager]

    def post(self, request):
        from .tasks import generate_daily_report

        task = generate_daily_report.delay()

        return Response(
            {
                "message": "Daily report generation started.",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )

class HealthCheckView(APIView):
    permission_classes = []

    def get(self, request):
        db_status = "ok"
        redis_status = "ok"

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_status = "error"

        # Check Redis
        try:
            redis_client = redis.Redis.from_url(
                settings.CELERY_BROKER_URL
            )
            redis_client.ping()
        except Exception:
            redis_status = "error"

        if db_status == "ok" and redis_status == "ok":
            return Response({
                "status": "ok",
                "database": "ok",
                "redis": "ok"
            }, status=200)

        return Response({
            "status": "error",
            "database": db_status,
            "redis": redis_status
        }, status=503)
        



