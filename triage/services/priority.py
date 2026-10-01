from django.utils import timezone
from datetime import timedelta

def get_priority(subject, description,category):
    text = f"{subject} {description}".lower()

    if "payment failed" in text:
        return "High"

    if "urgent" in text :
        return "High"

    if "not working" in text:
        return "High"

    if "refund" in text:
        return "High"

    if category in ["Payment", "Refund"]:
        return "Medium"

    return "Low"


def increase_priority(priority):
    levels = {
        "Low" : "Medium",
        "Medium" : "High",
        "High" : "High",
    }

    return levels[priority]

def get_priority_with_repeat_customer(ticket):
    priority = get_priority(
        ticket.subject,
        ticket.description,
        ticket.category,
    )

    seven_days_ago = timezone.now() - timedelta(days=7)

    recent_tickets = ticket.customer.ticket_set.filter(
        created_at__gte=seven_days_ago
    ).exclude(
        id=ticket.id
    ).count()

    if recent_tickets >= 2:
        priority = increase_priority(priority)

    return priority



