from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Customer, Ticket, TicketEvent, DailyReport

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = "__all__"

    def create(self, validated_data):
        from .services.priority import get_priority_with_repeat_customer

        ticket = Ticket(**validated_data)
        ticket.save()

        ticket.priority = get_priority_with_repeat_customer(ticket)
        ticket.save(update_fields=["priority"])

        return ticket    

    def update(self, instance, validated_data):
        from .services.ticket import update_ticket_status

        new_status = validated_data.get("status")

        if new_status and new_status != instance.status:
            update_ticket_status(instance, new_status)
            validated_data.pop("status")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

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



