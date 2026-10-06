from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

def send_ticket_event(ticket, event_name, data=None):
    channel_layer = get_channel_layer()

    message = {
        "type" : "ticket.event",
        "event" : event_name,
        "ticket_id" : ticket.ticket_id,
        "data" : data or {},
        "timestamp" : timezone.now().isoformat(),
    }

    #manager receive all ticket events
    async_to_sync(channel_layer.group_send)(
        "managers",
        message,
    )

    #Assigned agent receives events for their ticket
    if ticket.assigned_agent_id:
        async_to_sync(channel_layer.group_send)(
            f"agent_{ticket.assigned_agent_id}",
            message,
        )
        