from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from .models import DailyReport, Ticket


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

    count = tickets.update(sla_breached=True)

    return f"{count} tickets marked as SLA breached"


@shared_task
def generate_daily_report():
    today = timezone.localdate()

    new_tickets = Ticket.objects.filter(
        created_at__date=today
    ).count()

    resolved_tickets = Ticket.objects.filter(
        resolved_at__date=today
    ).count()

    sla_breaches = Ticket.objects.filter(
        sla_breached=True,
        created_at__date=today
    ).count()

    report, created = DailyReport.objects.update_or_create(
        report_date=today,
        defaults={
            "new_tickets": new_tickets,
            "resolved_tickets": resolved_tickets,
            "sla_breaches": sla_breaches,
        },
    )

    return f"Daily report generated for {today}"