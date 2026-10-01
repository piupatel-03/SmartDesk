from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView
from .views import (CustomerListCreateView, 
                    TicketListCreateView, CustomLoginView,
                    LogoutView,TicketDetailView, TicketStatsView,
                    DailyReportListView,HealthCheckView,)

urlpatterns = [
    path("customers/", CustomerListCreateView.as_view(), name="customer-list"),
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list"),
    path("auth/login/", CustomLoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("tickets/<int:pk>/", TicketDetailView.as_view(),name="ticket-detail"),
    path("stats/", TicketStatsView.as_view(), name="ticket-stats"),
    path("reports/", DailyReportListView.as_view(), name="daily-reports"),
    path("health/", HealthCheckView.as_view(), name="health"),
    
]

