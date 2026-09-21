from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    customer_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.customer_name}({self.customer_id})"

class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('Payment'),
        ('Technical'),
        ('Login'),
        ('Delivery'),
        ('Refund'),
        ('Account')
    ]

    STATUS_CHOICES = [
        
    ]

# Create your models here.
