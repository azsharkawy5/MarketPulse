import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


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


def test_user_registration_success(api_client: APIClient):
    register_url = reverse("accounts:register")
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
    }

    response = api_client.post(register_url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert "message" in response.data
    assert "user" in response.data
    assert "tokens" in response.data
    assert response.data["message"] == "User registered successfully"

    user_data = response.data["user"]
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
    assert user_data["first_name"] == "Test"
    assert user_data["last_name"] == "User"
    assert user_data["phone_number"] == "+1234567890"

    tokens = response.data["tokens"]
    assert "access" in tokens
    assert "refresh" in tokens

    created_user = User.objects.get(email="test@example.com")
    assert created_user.username == "testuser"
    assert created_user.is_email_verified is False


def test_user_registration_password_mismatch(api_client: APIClient):
    register_url = reverse("accounts:register")
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "differentpassword",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
    }

    response = api_client.post(register_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in response.data


def test_user_registration_missing_required_fields(api_client: APIClient):
    register_url = reverse("accounts:register")
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
    }

    response = api_client.post(register_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "first_name" in response.data
    assert "last_name" in response.data


def test_user_registration_duplicate_email(api_client: APIClient):
    register_url = reverse("accounts:register")
    User.objects.create_user(
        username="existinguser",
        email="test@example.com",
        password="testpass123",
        first_name="Existing",
        last_name="User",
    )

    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
    }

    response = api_client.post(register_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


def test_user_registration_weak_password(api_client: APIClient):
    register_url = reverse("accounts:register")
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "123",
        "password_confirm": "123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+1234567890",
    }

    response = api_client.post(register_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data


def test_user_login_success(api_client: APIClient, user: User):
    login_url = reverse("accounts:login")
    payload = {"email": "test@example.com", "password": "testpass123"}

    response = api_client.post(login_url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Login successful"
    assert "user" in response.data
    assert "tokens" in response.data
    assert response.data["user"]["email"] == "test@example.com"
    assert response.data["user"]["username"] == "testuser"
    assert "access" in response.data["tokens"]
    assert "refresh" in response.data["tokens"]


def test_user_login_invalid_credentials(api_client: APIClient, user: User):
    login_url = reverse("accounts:login")
    payload = {"email": "test@example.com", "password": "wrongpassword"}

    response = api_client.post(login_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in response.data


def test_user_login_nonexistent_user(api_client: APIClient):
    login_url = reverse("accounts:login")
    payload = {"email": "nonexistent@example.com", "password": "testpass123"}

    response = api_client.post(login_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in response.data


def test_user_login_missing_fields(api_client: APIClient):
    login_url = reverse("accounts:login")
    payload = {"email": "test@example.com"}

    response = api_client.post(login_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data


def test_user_login_inactive_user(api_client: APIClient, user: User):
    login_url = reverse("accounts:login")
    user.is_active = False
    user.save()

    payload = {"email": "test@example.com", "password": "testpass123"}

    response = api_client.post(login_url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in response.data


def test_get_profile_authenticated(api_client: APIClient, user: User):
    profile_url = reverse("accounts:profile")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = api_client.get(profile_url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == "testuser"
    assert response.data["email"] == "test@example.com"
    assert response.data["first_name"] == "Test"
    assert response.data["last_name"] == "User"
    assert response.data["phone_number"] == "+1234567890"


def test_get_profile_unauthenticated(api_client: APIClient):
    profile_url = reverse("accounts:profile")

    response = api_client.get(profile_url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_profile_authenticated(api_client: APIClient, user: User):
    profile_url = reverse("accounts:profile")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    update_data = {"first_name": "Updated", "last_name": "Name"}

    response = api_client.patch(profile_url, update_data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["first_name"] == "Updated"
    assert response.data["last_name"] == "Name"

    user.refresh_from_db()
    assert user.first_name == "Updated"
    assert user.last_name == "Name"


def test_update_profile_readonly_fields(api_client: APIClient, user: User):
    profile_url = reverse("accounts:profile")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    update_data = {
        "username": "newusername",
        "email": "newemail@example.com",
        "phone_number": "+9876543210",
    }

    response = api_client.patch(profile_url, update_data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == "testuser"
    assert response.data["email"] == "test@example.com"
    assert response.data["phone_number"] == "+1234567890"


def test_update_profile_unauthenticated(api_client: APIClient):
    profile_url = reverse("accounts:profile")
    update_data = {"first_name": "Updated", "last_name": "Name"}

    response = api_client.patch(profile_url, update_data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_authenticated_with_refresh_token(api_client: APIClient, user: User):
    logout_url = reverse("accounts:logout")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = api_client.post(
        logout_url, {"refresh_token": refresh_token}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Logout successful"


def test_logout_authenticated_without_refresh_token(api_client: APIClient, user: User):
    logout_url = reverse("accounts:logout")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = api_client.post(logout_url, {}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Logout successful"


def test_logout_unauthenticated(api_client: APIClient):
    logout_url = reverse("accounts:logout")

    response = api_client.post(logout_url, {}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logout_invalid_refresh_token(api_client: APIClient, user: User):
    logout_url = reverse("accounts:logout")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = api_client.post(
        logout_url, {"refresh_token": "invalid_token"}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == "Logout successful"


def test_token_refresh_success(api_client: APIClient, user: User):
    refresh_url = reverse("accounts:token_refresh")
    refresh = RefreshToken.for_user(user)
    response = api_client.post(refresh_url, {"refresh": str(refresh)}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


def test_token_refresh_invalid_token(api_client: APIClient):
    refresh_url = reverse("accounts:token_refresh")
    response = api_client.post(refresh_url, {"refresh": "invalid_token"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_refresh_missing_token(api_client: APIClient):
    refresh_url = reverse("accounts:token_refresh")
    response = api_client.post(refresh_url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
