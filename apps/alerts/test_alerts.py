import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from apps.alerts.models import Alert, AlertTrigger
from apps.stocks.models import Stock


User = get_user_model()


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        phone_number="+1234567890",
    )


@pytest.fixture
def authenticated_client(api_client: APIClient, user: User) -> APIClient:
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def stock() -> Stock:
    return Stock.objects.create(
        symbol="AAPL",
        name="Apple Inc.",
        type="Technology",
        is_active=True,
    )


@pytest.fixture
def alert(user: User, stock: Stock) -> Alert:
    return Alert.objects.create(
        user=user,
        stock=stock,
        alert_type="threshold",
        condition="above",
        threshold_price=Decimal("150.00"),
        notification_method="email",
        is_active=True,
    )


@pytest.fixture
def alert_trigger(alert: Alert) -> AlertTrigger:
    return AlertTrigger.objects.create(
        alert=alert,
        triggered_price=Decimal("151.00"),
        notification_sent=True,
    )


def test_create_alert_success(authenticated_client: APIClient, stock: Stock):
    url = reverse("alerts:alert-list")
    payload = {
        "stock": stock.id,
        "alert_type": "threshold",
        "condition": "above",
        "threshold_price": "150.00",
        "notification_method": "email",
    }

    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Alert.objects.count() == 1
    alert = Alert.objects.first()
    assert alert.stock.id == stock.id
    assert alert.alert_type == "threshold"
    assert alert.condition == "above"
    assert alert.threshold_price == Decimal("150.00")
    assert alert.notification_method == "email"
    assert alert.is_active is True


def test_create_alert_missing_fields(authenticated_client: APIClient, stock: Stock):
    url = reverse("alerts:alert-list")
    payload = {
        "stock": stock.id,
        "alert_type": "threshold",
    }

    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "condition" in response.data
    assert "threshold_price" in response.data


def test_create_alert_invalid_stock(authenticated_client: APIClient):
    url = reverse("alerts:alert-list")
    payload = {
        "stock": 999,  # Non-existent stock ID
        "alert_type": "threshold",
        "condition": "above",
        "threshold_price": "150.00",
        "notification_method": "email",
    }

    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "stock" in response.data


def test_create_alert_unauthenticated(api_client: APIClient, stock: Stock):
    url = reverse("alerts:alert-list")
    payload = {
        "stock": stock.id,
        "alert_type": "threshold",
        "condition": "above",
        "threshold_price": "150.00",
        "notification_method": "email",
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_alerts(authenticated_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-list")

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["id"] == alert.id
    assert response.data['results'][0]["stock"] == alert.stock.id
    assert response.data['results'][0]["alert_type"] == alert.alert_type
    assert response.data['results'][0]["condition"] == alert.condition
    assert Decimal(response.data['results'][0]["threshold_price"]) == alert.threshold_price


def test_list_alerts_unauthenticated(api_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-list")

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_alert_detail(authenticated_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-detail", kwargs={"pk": alert.id})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == alert.id
    assert response.data["stock"] == alert.stock.id
    assert response.data["alert_type"] == alert.alert_type
    assert response.data["condition"] == alert.condition
    assert Decimal(response.data["threshold_price"]) == alert.threshold_price
    assert response.data["notification_method"] == alert.notification_method
    assert response.data["is_active"] == alert.is_active


def test_retrieve_alert_detail_unauthenticated(api_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-detail", kwargs={"pk": alert.id})

    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_nonexistent_alert(authenticated_client: APIClient):
    url = reverse("alerts:alert-detail", kwargs={"pk": 999})

    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_alert(authenticated_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-detail", kwargs={"pk": alert.id})
    payload = {
        "condition": "below",
        "threshold_price": "140.00",
    }

    response = authenticated_client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    alert.refresh_from_db()
    assert alert.condition == "below"
    assert alert.threshold_price == Decimal("140.00")


def test_update_alert_unauthenticated(api_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-detail", kwargs={"pk": alert.id})
    payload = {
        "condition": "below",
        "threshold_price": "140.00",
    }

    response = api_client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_alert(authenticated_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-detail", kwargs={"pk": alert.id})

    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Alert.objects.count() == 0


def test_delete_alert_unauthenticated(api_client: APIClient, alert: Alert):
    url = reverse("alerts:alert-detail", kwargs={"pk": alert.id})

    response = api_client.delete(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Alert.objects.count() == 1


def test_toggle_alert_status(authenticated_client: APIClient, alert: Alert):
    url = reverse("alerts:toggle-alert", kwargs={"alert_id": alert.id})
    
    # Initially alert is active, toggle to inactive
    response = authenticated_client.post(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Alert deactivated successfully"
    assert response.data["is_active"] is False
    
    alert.refresh_from_db()
    assert alert.is_active is False
    
    # Toggle back to active
    response = authenticated_client.post(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Alert activated successfully"
    assert response.data["is_active"] is True
    
    alert.refresh_from_db()
    assert alert.is_active is True


def test_toggle_alert_status_unauthenticated(api_client: APIClient, alert: Alert):
    url = reverse("alerts:toggle-alert", kwargs={"alert_id": alert.id})
    
    response = api_client.post(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    alert.refresh_from_db()
    assert alert.is_active is True  # Should remain unchanged


def test_toggle_nonexistent_alert(authenticated_client: APIClient):
    url = reverse("alerts:toggle-alert", kwargs={"alert_id": 999})
    
    response = authenticated_client.post(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_alert_statistics(authenticated_client: APIClient, alert: Alert, alert_trigger: AlertTrigger):
    url = reverse("alerts:alert-statistics")
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_alerts"] == 1
    assert response.data["active_alerts"] == 1
    assert response.data["total_triggers"] == 1
    assert "recent_triggers" in response.data
    assert "alert_types" in response.data
    assert response.data["alert_types"]["threshold"] == 1
    assert response.data["alert_types"]["duration"] == 0


def test_alert_statistics_unauthenticated(api_client: APIClient):
    url = reverse("alerts:alert-statistics")
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_alert_triggers(authenticated_client: APIClient, alert_trigger: AlertTrigger):
    url = reverse("alerts:trigger-list")
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["id"] == alert_trigger.id
    assert response.data['results'][0]["alert"] == alert_trigger.alert.id
    assert Decimal(response.data['results'][0]["triggered_price"]) == alert_trigger.triggered_price
    assert response.data['results'][0]["notification_sent"] == alert_trigger.notification_sent


def test_list_alert_triggers_unauthenticated(api_client: APIClient):
    url = reverse("alerts:trigger-list")
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_alert_trigger(authenticated_client: APIClient, alert_trigger: AlertTrigger):
    url = reverse("alerts:trigger-detail", kwargs={"pk": alert_trigger.id})
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == alert_trigger.id
    assert response.data["alert"] == alert_trigger.alert.id
    assert Decimal(response.data["triggered_price"]) == alert_trigger.triggered_price
    assert response.data["notification_sent"] == alert_trigger.notification_sent


def test_retrieve_alert_trigger_unauthenticated(api_client: APIClient, alert_trigger: AlertTrigger):
    url = reverse("alerts:trigger-detail", kwargs={"pk": alert_trigger.id})
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
