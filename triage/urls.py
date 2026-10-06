from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomerListCreateView,
    TicketListCreateView,
    CustomLoginView,
    LogoutView,
    TicketDetailView,
    TicketStatsView,
    TicketAssignView,
    TicketTransitionView,
    DailyReportListView,
    DailyReportGenerateView,
    HealthCheckView,
)


urlpatterns = [
    path(
        "customers/",CustomerListCreateView.as_view(),
        name="customer-list",
    ),

    path(
        "tickets/",TicketListCreateView.as_view(),
        name="ticket-list",
    ),

    path(
        "auth/login/",CustomLoginView.as_view(),
        name="login",
    ),

    path(
        "auth/refresh/",TokenRefreshView.as_view(),
        name="token-refresh",
    ),

    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="logout",
    ),

    path(
        "tickets/<int:pk>/",TicketDetailView.as_view(),
        name="ticket-detail",
    ),

    path(
        "tickets/<int:pk>/assign/",TicketAssignView.as_view(),
        name="ticket-assign",
    ),

    path(
        "tickets/<int:pk>/transition/",TicketTransitionView.as_view(),
        name="ticket-transition",
    ),

    path(
        "stats/",TicketStatsView.as_view(),
        name="ticket-stats",
    ),

    path(
        "reports/daily/",DailyReportListView.as_view(),
        name="daily-reports",
    ),

    path(
        "reports/daily/generate/",DailyReportGenerateView.as_view(),
        name="daily-report-generate",
    ),

    path(
        "health/",HealthCheckView.as_view(),
        name="health",
    ),
]

