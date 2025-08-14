from django.conf import settings
from django.db import models


class Alert(models.Model):
    """
    Model to store user-defined stock price alerts.
    """

    ALERT_TYPES = [
        ("threshold", "Threshold Alert"),
        ("duration", "Duration Alert"),
    ]

    CONDITIONS = [
        ("above", "Above"),
        ("below", "Below"),
        ("equals", "Equals"),
    ]

    #  Method may be extended in the future to support more notification methods
    NOTIFICATION_METHODS = [
        ("email", "Email"),
        ("console", "Console Notification"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts"
    )
    stock = models.ForeignKey(
        "stocks.Stock", on_delete=models.CASCADE, related_name="alerts"
    )
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    condition = models.CharField(max_length=10, choices=CONDITIONS)
    threshold_price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = models.PositiveIntegerField(default=0)
    notification_method = models.CharField(
        max_length=10, choices=NOTIFICATION_METHODS, default="email"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stock', 'is_active']),
        ]


class AlertTrigger(models.Model):
    """
    Model to track when alerts have been triggered.
    """

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="triggers")
    triggered_price = models.DecimalField(max_digits=10, decimal_places=2)
    triggered_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    class Meta:
        indexes = [
            models.Index(fields=['alert', '-triggered_at']),
            models.Index(fields=['triggered_at']),
        ]


class AlertCheck(models.Model):
    """
    Model to track alert condition checks for duration alerts.
    """

    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="checks")
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    condition_met = models.BooleanField()
    checked_at = models.DateTimeField(auto_now_add=True)
    duration_start = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['alert', '-checked_at']),
            models.Index(fields=['checked_at']),
        ]