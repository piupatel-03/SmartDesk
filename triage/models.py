from celery import shared_task
from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Customer(models.Model):
    customer_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.customer_name}({self.customer_id})"

class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('Payment', 'Payment'),
        ('Technical', 'Technical'),
        ('Login', 'Login'),
        ('Delivery', 'Delivery'),
        ('Refund', 'Refund'),
        ('Account', 'Account')
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]

    CHANNEL_CHOICES = [
        ('Email', 'Email'),
        ('Chat', 'Chat'),
        ('Phone', 'Phone'),
        ('WhatsApp', 'WhatsApp'),
    ]

    ticket_id = models.CharField(max_length=50, unique=True)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )

    subject = models.CharField(max_length=255)
    description = models.TextField()

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Open'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Low'
    )

    channel = models.CharField(
        max_length=50,
        choices=CHANNEL_CHOICES
    )

    assigned_agent = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField()
    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    sla_breached = models.BooleanField(default=False)

    def __str__(self):
        return self.ticket_id

class TicketEvent(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='events'
    )

    event_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    careated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.report_date)


class DailyReport(models.Model):

    report_date = models.DateField(unique=True)
    new_tickets = models.IntegerField(default=0)
    resolved_tickets = models.IntegerField(default=0)
    sla_breaches = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.report_date)


