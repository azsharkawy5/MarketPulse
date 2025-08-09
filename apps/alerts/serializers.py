from rest_framework import serializers
from .models import Alert, AlertTrigger, AlertCheck
from apps.stocks.serializers import StockSerializer


class AlertSerializer(serializers.ModelSerializer):
    """
    Serializer for alert creation and management.
    """

    stock_details = StockSerializer(source="stock", read_only=True)
    description = serializers.CharField(read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id",
            "user",
            "stock",
            "stock_details",
            "alert_type",
            "condition",
            "threshold_price",
            "duration_hours",
            "notification_method",
            "is_active",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def validate(self, attrs):
        # Validate duration_hours for duration alerts
        if (
            attrs.get("alert_type") == "duration"
            and attrs.get("duration_hours", 0) <= 0
        ):
            raise serializers.ValidationError(
                "Duration alerts must have duration_hours > 0"
            )

        # Validate threshold_price
        if attrs.get("threshold_price", 0) <= 0:
            raise serializers.ValidationError("Threshold price must be greater than 0")

        return attrs


class AlertTriggerSerializer(serializers.ModelSerializer):
    """
    Serializer for alert trigger history.
    """

    alert_details = AlertSerializer(source="alert", read_only=True)

    class Meta:
        model = AlertTrigger
        fields = [
            "id",
            "alert",
            "alert_details",
            "triggered_price",
            "triggered_at",
            "notification_sent",
            "notification_sent_at",
            "error_message",
        ]
        read_only_fields = [
            "triggered_at",
            "notification_sent",
            "notification_sent_at",
            "error_message",
        ]


class AlertCheckSerializer(serializers.ModelSerializer):
    """
    Serializer for alert condition checks.
    """

    class Meta:
        model = AlertCheck
        fields = [
            "id",
            "alert",
            "current_price",
            "condition_met",
            "checked_at",
            "duration_start",
        ]
        read_only_fields = ["checked_at"]


class AlertSummarySerializer(serializers.ModelSerializer):
    """
    Serializer for alert summary with trigger count.
    """

    stock_details = StockSerializer(source="stock", read_only=True)
    trigger_count = serializers.SerializerMethodField()
    last_triggered = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id",
            "stock",
            "stock_details",
            "alert_type",
            "condition",
            "threshold_price",
            "duration_hours",
            "notification_method",
            "is_active",
            "trigger_count",
            "last_triggered",
            "created_at",
        ]

    def get_trigger_count(self, obj):
        return obj.triggers.count()

    def get_last_triggered(self, obj):
        last_trigger = obj.triggers.first()
        return last_trigger.triggered_at if last_trigger else None


class CreateAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new alerts.
    """

    class Meta:
        model = Alert
        fields = [
            "stock",
            "alert_type",
            "condition",
            "threshold_price",
            "duration_hours",
            "notification_method",
        ]

    def validate(self, attrs):
        # Validate duration_hours for duration alerts
        if (
            attrs.get("alert_type") == "duration"
            and attrs.get("duration_hours", 0) <= 0
        ):
            raise serializers.ValidationError(
                "Duration alerts must have duration_hours > 0"
            )

        # Validate threshold_price
        if attrs.get("threshold_price", 0) <= 0:
            raise serializers.ValidationError("Threshold price must be greater than 0")

        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
