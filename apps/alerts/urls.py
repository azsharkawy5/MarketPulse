from django.urls import path
from . import views

app_name = "alerts"

urlpatterns = [
    path("alerts/", views.AlertListView.as_view(), name="alert-list"),
    path("alerts/<int:pk>/", views.AlertDetailView.as_view(), name="alert-detail"),
    path(
        "alerts/<int:alert_id>/toggle/",
        views.ToggleAlertStatusView.as_view(),
        name="toggle-alert",
    ),
    path(
        "alerts/statistics/",
        views.AlertStatisticsView.as_view(),
        name="alert-statistics",
    ),
    path("alerts/checks/", views.AlertCheckListView.as_view(), name="alert-check-list"),
    path("triggers/", views.AlertTriggerListView.as_view(), name="trigger-list"),
    path(
        "triggers/<int:pk>/",
        views.AlertTriggerDetailView.as_view(),
        name="trigger-detail",
    ),
]
