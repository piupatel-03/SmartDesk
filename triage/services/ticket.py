from django.utils import timezone
from triage.models import Ticket, TicketEvent

ALLOWED_TRANSITIONS = {
    "Open" : ["In Progress"],
    "In Progress" : ["Resolved"],
    "Resolved" : ["In Progress", "Closed"],
    "Closed" : [],
}

def update_ticket_status(ticket, new_status):
    old_status = ticket.status

    if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
        raise ValueError(
            f"Cannot change status from {old_status} to {new_status}"
        )

    ticket.status = new_status

    if new_status == "Resolved":
        ticket.resolved_at = timezone.now()


    elif old_status == "Resolved" and new_status == "In Progress":
        ticket.resolved_at = None

    ticket.save()

    TicketEvent.objects.create(
        ticket=ticket,
        event_type="STATUS_CHANGED",
        description=f"Status changed from {old_status} to {new_status}"
    )

    return ticket
