from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Customer, Ticket, TicketEvent, DailyReport

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Ticket
        fields = "__all__"    # include all model fields in api

class TicketEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketEvent
        fields = "__all__"

class DailyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReport
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]



