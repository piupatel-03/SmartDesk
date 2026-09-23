import csv
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import User
from triage.models import Ticket, Customer, Ticket
from triage.services.priority import get_priority



class Command(BaseCommand):
    help = "Import tickets from a CSV file"

    def add_arguments(self,parser):
        parser.add_argument("csv_file")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        rows_read = 0
        imported = 0
        skipped = 0
        flagged = 0


    

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
                category = row["category"].strip()
                status = row["status"].strip()
                channel = row["channel"].strip()
                created_at = row["created_at"].strip()
                resolved_at = row["resolved_at"].strip()

                if Ticket.objects.filter(ticket_id=ticket_id).exists():
                    skipped +=1
                    continue

                if not ticket_id or not customer_id or not email:
                    flagged += 1
                    continue

                if category not in dict(Ticket.CATEGORY_CHOICES):
                    flagged += 1
                    continue

                if status not in dict(Ticket.STATUS_CHOICES):
                    flagged += 1
                    continue

                if channel not in dict(Ticket.CHANNEL_CHOICES):
                    flagged += 1
                    continue

                created_datetime = parse_datetime(created_at)
                if created_datetime is None:
                    flagged += 1
                    continue

                resolved_datetime = None

                if resolved_at:
                    resolved_datetime = parse_datetime(resolved_at)

                    customer, created = Customer.objects.get_or_create(
                        customer_id=customer_id,
                        defaults={
                            "customer_name": customer_name,
                            "email" : email,
                        },
                    )

                    priority = get_priority(
                        subject,
                        description,
                        category,
                    )

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

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"ROWS read: {rows_read}"
                        )
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Imported: {imported}"
                        )
                    )

                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped: {skipped}"
                        )
                    )

                    self.stdout.write(
                        self.style.WARNING(
                            f"Flagged: {flagged}"
                        )
                    )



