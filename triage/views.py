from django.shortcuts import render

from rest_framework import generics  # import DRF api views
from .models import Customer, Ticket
from .serializers import CustomerSerializer, TicketSerializer 

class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class TicketListCreateView(generics.ListCreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer






