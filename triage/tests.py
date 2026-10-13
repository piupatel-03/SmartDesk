from django.contrib.auth.models import User, Group
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Customer, Ticket
from .services.priority import get_priority
from .services.ticket import update_ticket_status


class SmartDeskTests(APITestCase):

    def setUp(self):
        self.agent_group, _ = Group.objects.get_or_create(
            name="Agent"
        )

        self.agent = User.objects.create_user(
            username="test_agent",
            password="testpass123"
        )
        self.agent.groups.add(self.agent_group)

        self.other_agent = User.objects.create_user(
            username="other_agent",
            password="testpass123"
        )
        self.other_agent.groups.add(self.agent_group)

        self.customer = Customer.objects.create(
            customer_id="TEST-C001",
            customer_name="Test Customer",
            email="test@example.com"
        )

        self.ticket = Ticket.objects.create(
            ticket_id="TEST-T001",
            customer=self.customer,
            subject="Payment failed",
            description="Payment failed during checkout",
            category="Payment",
            status="Open",
            priority="High",
            channel="Email",
            assigned_agent=self.agent,
            created_at="2026-09-30T10:00:00Z",
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}"
        )

    # 1
    def test_health_endpoint(self):
        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)

    # 2
    def test_agent_can_access_assigned_ticket(self):
        self.authenticate(self.agent)

        response = self.client.get(
            f"/api/tickets/{self.ticket.id}/"
        )

        self.assertEqual(response.status_code, 200)

    # 3
    def test_agent_cannot_access_other_ticket(self):
        self.authenticate(self.other_agent)

        response = self.client.get(
            f"/api/tickets/{self.ticket.id}/"
        )

        self.assertEqual(response.status_code, 404)

    # 4
    def test_status_transition(self):
        update_ticket_status(
            self.ticket,
            "In Progress"
        )

        self.assertEqual(
            self.ticket.status,
            "In Progress"
        )

    # 5
    def test_priority_payment_failed(self):
        priority = get_priority(
            "Payment failed",
            "Customer payment failed",
            "Payment"
        )

        self.assertEqual(priority, "High")

    # 6
    def test_login(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "test_agent",
                "password": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    # 7
    def test_refresh_token(self):
        refresh = RefreshToken.for_user(self.agent)

        response = self.client.post(
            "/api/auth/refresh/",
            {
                "refresh": str(refresh),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    # 8
    def test_agent_cannot_access_manager_stats(self):
        self.authenticate(self.agent)

        response = self.client.get("/api/stats/")

        self.assertEqual(response.status_code, 403)

    # 9
    def test_invalid_status_transition(self):
        with self.assertRaises(ValueError):
            update_ticket_status(
                self.ticket,
                "Closed"
            )

    # 10
    def test_ticket_event_created(self):
        from .models import TicketEvent

        update_ticket_status(
            self.ticket,
            "In Progress"
        )

        event_exists = TicketEvent.objects.filter(
            ticket=self.ticket,
            event_type="STATUS_CHANGED"
        ).exists()

        self.assertTrue(event_exists)