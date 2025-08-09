from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Alert, AlertTrigger, AlertCheck
from .serializers import (
    AlertSerializer,
    AlertTriggerSerializer,
    AlertCheckSerializer,
    AlertSummarySerializer,
    CreateAlertSerializer,
    AlertCheckSerializer,
)


class AlertListView(generics.ListCreateAPIView):
    """
    View to list and create alerts for the authenticated user.
    """

    serializer_class = AlertSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateAlertSerializer
        return AlertSummarySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, and delete a specific alert.
    """

    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)


class AlertTriggerListView(generics.ListAPIView):
    """
    View to list alert triggers for the authenticated user.
    """

    serializer_class = AlertTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertTrigger.objects.filter(alert__user=self.request.user)


class AlertTriggerDetailView(generics.RetrieveAPIView):
    """
    View to retrieve a specific alert trigger.
    """

    serializer_class = AlertTriggerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertTrigger.objects.filter(alert__user=self.request.user)


class AlertCheckListView(generics.ListAPIView):
    """
    View to list alert checks for the authenticated user.
    """

    serializer_class = AlertCheckSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertCheck.objects.filter(alert__user=self.request.user)


class ToggleAlertStatusView(APIView):
    """Toggle alert active/inactive status for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, alert_id):
        alert = get_object_or_404(Alert, id=alert_id, user=request.user)
        alert.is_active = not alert.is_active
        alert.save()

        return Response(
            {
                "message": f'Alert {"activated" if alert.is_active else "deactivated"} successfully',
                "is_active": alert.is_active,
            }
        )


class AlertStatisticsView(APIView):
    """Get alert statistics for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_alerts = Alert.objects.filter(user=request.user)

        total_alerts = user_alerts.count()
        active_alerts = user_alerts.filter(is_active=True).count()
        total_triggers = AlertTrigger.objects.filter(alert__user=request.user).count()

        # Get alerts by type
        threshold_alerts = user_alerts.filter(alert_type="threshold").count()
        duration_alerts = user_alerts.filter(alert_type="duration").count()

        # Get recent triggers (last 7 days)
        from django.utils import timezone
        from datetime import timedelta

        recent_triggers = AlertTrigger.objects.filter(
            alert__user=request.user,
            triggered_at__gte=timezone.now() - timedelta(days=7),
        ).count()

        return Response(
            {
                "total_alerts": total_alerts,
                "active_alerts": active_alerts,
                "total_triggers": total_triggers,
                "recent_triggers": recent_triggers,
                "alert_types": {
                    "threshold": threshold_alerts,
                    "duration": duration_alerts,
                },
            }
        )
