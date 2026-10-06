from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from .models import DailyReport, Ticket, TicketEvent
from .services.notifications import send_ticket_event


@shared_task
def test_celery_task():
    return "Celery is working!"


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def send_ticket_acknowledgement(self, ticket_id, customer_email):
    send_mail(
        subject=f"Ticket {ticket_id} received",
        message=(
            f"Your ticket {ticket_id} has been received successfully. "
            "Our support team will review it shortly."
        ),
        from_email=None,
        recipient_list=[customer_email],
    )

    return f"Acknowledgement sent for {ticket_id}"


@shared_task
def scan_sla_breaches():
    cutoff = timezone.now() - timedelta(hours=24)

    tickets = Ticket.objects.filter(
        status__in=["Open", "In Progress"],
        created_at__lt=cutoff,
        sla_breached=False,
    )

    count = 0

    for ticket in tickets:
        ticket.sla_breached = True
        ticket.save(update_fields=["sla_breached"])

        TicketEvent.objects.create(
            ticket=ticket,
            event_type="SLA_BREACHED",
            description="Ticket breached the 24-hour SLA.",
        )

        send_ticket_event(
            ticket,
            "ticket.sla_breached",
            {
                "status" : ticket.status,
                "priority" : ticket.priority,
                "sla_breached" : True,
            }
        )
        count +=1

    return f"{count} tickets marked as SLA breached"


@shared_task
def generate_daily_report():
    today = timezone.localdate()
    report_date = today - timezone.timedelta(days=1)

    new_tickets = Ticket.objects.filter(
        created_at__date=report_date
    )

    resolved_tickets = Ticket.objects.filter(
        resolved_at__date=report_date
    )

    sla_breaches = Ticket.objects.filter(
        sla_breached=True,
        created_at__date=report_date
    ).count()

    category_counts = dict(
        new_tickets.values("category")
        .annotate(count=Count("id"))
        .values_list("category", "count")
    )

    priority_counts = dict(
        new_tickets.values("priority")
        .annotate(count=Count("id"))
        .values_list("priority", "count")
    )

    report, created = DailyReport.objects.update_or_create(
        report_date=report_date,
        defaults={
            "new_tickets": new_tickets.count(),
            "resolved_tickets": resolved_tickets.count(),
            "sla_breaches": sla_breaches,
            "category_counts": category_counts,
            "priority_counts": priority_counts,
        },
    )

    return f"Daily report generated for {report_date}"

@shared_task
def process_public_ticket(ticket_data):
    from .serializers import TicketSerializer

    serializer = TicketSerializer(data=ticket_data)
    serializer.is_valid(raise_exception=True)

    ticket = serializer.save()

    return {
        "ticket_id": ticket.ticket_id,
    }