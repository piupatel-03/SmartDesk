import csv

from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime
from triage.models import Ticket, Customer
from triage.services.priority import get_priority




def parse_csv_datetime(value):
    value = value.strip()

    if not value:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%b %d, %Y %I:%M %p",
    ]
    

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return None

def clean_category(category):
    value = category.strip().lower()

    category_map = {
        "payment": "Payment",
        "payments": "Payment",
        "paymnt": "Payment",
        "paymnet": "Payment",

        "technical" : "Technical",
        "tech" : "Technical",
        "technical issue" : "Technical",
        "tech issue" : "Technical",

        "login" : "Login",
        "log-in" : "Login",
        "login issue" : "Login",
        "login issues" : "Login",

        "delivery" : "Delivery",
        "shipping/delivery" : "Delivery",
        "delivery" : "Delivery",

        "refund" : "Refund",
        "refund request" : "Refund",
        "refnd" : "Refund",

        "account" : "Account",
        "account" : "Account",
        "account settings" : "Account",

    }

    return category_map.get(value)
  
def clean_status(status):
    value = status.strip().lower()

    status_map = {
        "open" : "Open",
        "in progress" : "In Progress",
        "in-progress" : "In Progress",
        "wip" : "In Progress",
        "resolved" : "Resolved",
        "closed" : "Closed",
        "done" : "Resolved",

    }

    return status_map.get(value)

def clean_channel(channel):
    value = channel.strip().lower()

    channel_map = {
        "email": "Email",
        "e-mail": "Email",
        "chat": "Chat",
        "live chat": "Chat",
        "phone": "Phone",
        "call": "Phone",
        "whatsapp": "WhatsApp",
        "wa" : "WhatsApp",
    }

    return channel_map.get(value)



class Command(BaseCommand):
    help = "Import tickets from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        rows_read = 0
        imported = 0
        skipped = 0
        flagged = 0

        flag_reasons = []

        with open(csv_file, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            for row in reader:
                rows_read += 1

                ticket_id = row["ticket_id"].strip()
                customer_id = row["customer_id"].strip()
                customer_name = row["customer_name"].strip()
                email = row["email"].strip()
                subject = row["subject"].strip()
                description = row["description"].strip()
                category = clean_category(row["category"])
                status = clean_status(row["status"])
                channel = clean_channel(row["channel"])
                created_at = row["created_at"].strip()
                resolved_at = row["resolved_at"].strip()

                # Check duplicate ticket
                if Ticket.objects.filter(ticket_id=ticket_id).exists():
                    skipped += 1
                    continue

                # Validate required fields
                if not ticket_id:
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: missing ticket_id"
                    )
                    continue

                if not customer_id:
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: missing customer_id"
                    )
                    continue

                if not email:
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: missing email"
                    )
                    continue

                # Validate category
                if category not in dict(Ticket.CATEGORY_CHOICES):
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: invalid category - {category}"
                    )
                    continue

                # Validate status
                if status not in dict(Ticket.STATUS_CHOICES):
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: invalid status - {status}"
                    )
                    continue

                # Validate channel
                if channel not in dict(Ticket.CHANNEL_CHOICES):
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: invalid channel - {channel}"
                    )
                    continue

                # Parse created_at
                created_datetime = parse_csv_datetime(created_at)

                if created_datetime is None:
                    flagged += 1
                    flag_reasons.append(
                        f"{ticket_id}: invalid created_at - {created_at}"
                    )
                    continue

                # Convert CSV IST time to timezone-aware datetime
                if created_datetime.tzinfo is None:
                    created_datetime = make_aware(
                        created_datetime,
                        get_current_timezone(),
                    )

                # Parse resolved_at
                resolved_datetime = None

                if resolved_at:
                    resolved_datetime = parse_csv_datetime(resolved_at)

                    if resolved_datetime is None:
                        flagged += 1
                        flag_reasons.append(
                            f"{ticket_id}: invalid resolved_at - {resolved_at}"
                        )
                        continue

                    if resolved_datetime.tzinfo is None:
                        resolved_datetime = make_aware(
                            resolved_datetime,
                            get_current_timezone(),
                        )

                # Create or get customer
                customer, created = Customer.objects.get_or_create(
                    customer_id=customer_id,
                    defaults={
                        "customer_name": customer_name,
                        "email": email,
                    },
                )

                # Calculate priority
                priority = get_priority(
                    subject,
                    description,
                    category,
                )

                # Create ticket
                Ticket.objects.create(
                    ticket_id=ticket_id,
                    customer=customer,
                    subject=subject,
                    description=description,
                    category=category,
                    status=status,
                    priority=priority,
                    channel=channel,
                    created_at=created_datetime,
                    resolved_at=resolved_datetime,
                )

                imported += 1

        # Final summary
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(f"ROWS read: {rows_read}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"Imported: {imported}")
        )
        self.stdout.write(
            self.style.WARNING(f"Skipped: {skipped}")
        )
        self.stdout.write(
            self.style.WARNING(f"Flagged: {flagged}")
        )

        # Show reasons for flagged rows
        if flag_reasons:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("Flagged rows:")
            )

            for reason in flag_reasons:
                self.stdout.write(f"- {reason}")