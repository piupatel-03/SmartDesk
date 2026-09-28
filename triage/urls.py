from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (CustomerListCreateView, TicketListCreateView)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list"),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list"),
    path("token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    
]

