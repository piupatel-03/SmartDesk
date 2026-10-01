from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsManagerOrAgent
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics  # import DRF api views
from rest_framework.permissions import IsAuthenticated
from .models import Customer, Ticket, DailyReport
from django.db.models import Count
from .authentication import CustomTokenObtainPairSerializer
from .serializers import CustomerSerializer, TicketSerializer, DailyReportSerializer 

class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

class TicketListCreateView(generics.ListCreateAPIView):
    serializer_class = TicketSerializer
    permission_classes = [IsManagerOrAgent]

    filterset_fields = ["status", "category", "priority", "channel"]
    search_fields = ["ticket_id", "subject", "description"]
    ordering_fields = ["created_at", "resolved_at", "priority", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="Manager").exists():
            return Ticket.objects.all()

        if user.groups.filter(name="Agent").exists():
            return Ticket.objects.filter(assigned_agent=user)

        return Ticket.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.groups.filter(name="Agent").exists():
            serializer.save(assigned_agent=user)
        else:
            serializer.save()

    

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
        if instance.status == "Closed":
            from rest_framework.exceptions import ValidationError

            raise ValidationError(
                {"detail": "Closed tickets cannot be deleted."}
            )

        instance.delete()

        
class TicketStatsView(APIView):
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
    permission_classes = [IsManagerOrAgent]


class HealthCheckView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({
            "status": "ok"
        })
        



