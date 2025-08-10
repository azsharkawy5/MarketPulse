import logging
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from celery import shared_task
from .models import Alert, AlertTrigger, AlertCheck

logger = logging.getLogger(__name__)


@shared_task
def process_alerts():
    """
    Process all active alerts and check if conditions are met.
    """
    active_alerts = Alert.objects.filter(is_active=True)

    for alert in active_alerts:
        try:
            if alert.alert_type == "threshold":
                process_threshold_alert.delay(alert.id)
            elif alert.alert_type == "duration":
                process_duration_alert.delay(alert.id)
        except Exception as e:
            logger.error(f"Error processing alert {alert.id}: {e}")


@shared_task
def process_threshold_alert(alert_id):
    """
    Process a threshold alert.
    """
    try:
        alert = Alert.objects.get(id=alert_id, is_active=True)
        latest_price = alert.stock.prices.first()

        if not latest_price:
            logger.warning(f"No price data available for {alert.stock.symbol}")
            return

        current_price = latest_price.close_price
        condition_met = False

        # Check if condition is met
        if alert.condition == "above":
            condition_met = current_price > alert.threshold_price
        elif alert.condition == "below":
            condition_met = current_price < alert.threshold_price
        elif alert.condition == "equals":
            condition_met = current_price == alert.threshold_price

        if condition_met:
            # Check if we already triggered this alert recently (within 1 hour)
            recent_trigger = AlertTrigger.objects.filter(
                alert=alert,
                triggered_at__gte=timezone.now() - timezone.timedelta(hours=1),
            ).first()

            if not recent_trigger:
                # Create trigger record
                trigger = AlertTrigger.objects.create(
                    alert=alert, triggered_price=current_price
                )

                # Send notification
                send_alert_notification.delay(trigger.id)

                logger.info(
                    f"Threshold alert triggered for {alert.stock.symbol} at ${current_price}"
                )

    except Alert.DoesNotExist:
        logger.warning(f"Alert {alert_id} not found or inactive")
    except Exception as e:
        logger.error(f"Error processing threshold alert {alert_id}: {e}")


@shared_task
def process_duration_alert(alert_id):
    """
    Process a duration alert.
    """
    try:
        alert = Alert.objects.get(id=alert_id, is_active=True)
        latest_price = alert.stock.prices.first()

        if not latest_price:
            logger.warning(f"No price data available for {alert.stock.symbol}")
            return

        current_price = latest_price.close_price
        condition_met = False

        # Check if condition is met
        if alert.condition == "above":
            condition_met = current_price > alert.threshold_price
        elif alert.condition == "below":
            condition_met = current_price < alert.threshold_price
        elif alert.condition == "equals":
            condition_met = current_price == alert.threshold_price

        # Record the check
        check = AlertCheck.objects.create(
            alert=alert, current_price=current_price, condition_met=condition_met
        )

        if condition_met:
            # Check if this is the start of a new condition period
            previous_check = (
                AlertCheck.objects.filter(alert=alert, condition_met=True)
                .exclude(id=check.id)
                .order_by("-checked_at")
                .first()
            )

            if not previous_check or not check.duration_start:
                # Start tracking duration
                check.duration_start = timezone.now()
                check.save()

            # Check if duration requirement is met
            if check.duration_start:
                duration_elapsed = timezone.now() - check.duration_start
                required_duration = timezone.timedelta(hours=alert.duration_hours)

                if duration_elapsed >= required_duration:
                    # Check if we already triggered this alert recently (within 1 hour)
                    recent_trigger = AlertTrigger.objects.filter(
                        alert=alert,
                        triggered_at__gte=timezone.now() - timezone.timedelta(hours=1),
                    ).first()

                    if not recent_trigger:
                        # Create trigger record
                        trigger = AlertTrigger.objects.create(
                            alert=alert, triggered_price=current_price
                        )

                        # Send notification
                        send_alert_notification.delay(trigger.id)

                        logger.info(
                            f"Duration alert triggered for {alert.stock.symbol} at ${current_price}"
                        )
        else:
            # Reset duration tracking if condition is not met
            if check.duration_start:
                check.duration_start = None
                check.save()

    except Alert.DoesNotExist:
        logger.warning(f"Alert {alert_id} not found or inactive")
    except Exception as e:
        logger.error(f"Error processing duration alert {alert_id}: {e}")


@shared_task
def send_alert_notification(trigger_id):
    """
    Send notification for an alert trigger.
    """
    try:
        # Use select_for_update to lock the row during this transaction
        from django.db import transaction
        
        with transaction.atomic():
            # Lock the row to prevent concurrent access
            trigger = AlertTrigger.objects.select_for_update().get(id=trigger_id)
            alert = trigger.alert
            
            # Check if notification has already been sent
            if trigger.notification_sent:
                logger.info(f"Notification for trigger {trigger_id} already sent, skipping")
                return
                
            # Mark notification as being processed immediately to prevent duplicate processing
            trigger.notification_sent = True
            trigger.notification_sent_at = timezone.now()
            trigger.save()
        
        # Now that we've marked it as sent, process the notification
        if alert.notification_method == "email":
            # Call directly instead of using delay to ensure sequential processing
            send_email_notification(trigger_id)
        elif alert.notification_method == "console":
            # Call directly instead of using delay to ensure sequential processing
            send_console_notification(trigger_id)

    except AlertTrigger.DoesNotExist:
        logger.warning(f"Alert trigger {trigger_id} not found")
    except Exception as e:
        logger.error(f"Error sending notification for trigger {trigger_id}: {e}")


@shared_task
def send_email_notification(trigger_id):
    """
    Send email notification for an alert trigger.
    """
    try:
        trigger = AlertTrigger.objects.get(id=trigger_id)
        alert = trigger.alert
        user = alert.user

        if not settings.EMAIL_HOST_USER:
            logger.error("Email configuration not set up")
            return

        subject = f"Stock Alert: {alert.stock.symbol} {alert.condition} ${alert.threshold_price}"

        context = {
            "user": user,
            "alert": alert,
            "trigger": trigger,
            "stock": alert.stock,
        }

        # Simple text email
        message = f"""
        Hello {user.first_name or user.username},
        
        Your stock alert has been triggered!
        
        Stock: {alert.stock.symbol} ({alert.stock.name})
        Current Price: ${trigger.triggered_price}
        Triggered At: {trigger.triggered_at}
        
        Best regards,
        Stock Alert System
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Email notification sent for alert {alert.id}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            trigger.error_message = str(e)
            trigger.save()

    except AlertTrigger.DoesNotExist:
        logger.warning(f"Alert trigger {trigger_id} not found")
    except Exception as e:
        logger.error(f"Error sending email notification for trigger {trigger_id}: {e}")


@shared_task
def send_console_notification(trigger_id):
    """
    Send console notification for an alert trigger.
    """
    try:
        trigger = AlertTrigger.objects.get(id=trigger_id)
        alert = trigger.alert
        user = alert.user

        message = f"""
        ===== STOCK ALERT TRIGGERED =====
        User: {user.email}
        Stock: {alert.stock.symbol} ({alert.stock.name})
        Current Price: ${trigger.triggered_price}
        Triggered At: {trigger.triggered_at}
        =================================
        """

        print(message)
        logger.info(f"Console notification sent for alert {alert.id}")

    except AlertTrigger.DoesNotExist:
        logger.warning(f"Alert trigger {trigger_id} not found")
    except Exception as e:
        logger.error(
            f"Error sending console notification for trigger {trigger_id}: {e}"
        )


@shared_task
def cleanup_old_alert_data():
    """
    Clean up old alert triggers and checks to prevent database bloat.
    """
    from datetime import timedelta

    # Keep triggers for 90 days
    trigger_cutoff = timezone.now() - timedelta(days=90)
    deleted_triggers = AlertTrigger.objects.filter(
        triggered_at__lt=trigger_cutoff
    ).delete()[0]

    # Keep checks for 30 days
    check_cutoff = timezone.now() - timedelta(days=30)
    deleted_checks = AlertCheck.objects.filter(checked_at__lt=check_cutoff).delete()[0]

    logger.info(
        f"Cleaned up {deleted_triggers} old triggers and {deleted_checks} old checks"
    )
