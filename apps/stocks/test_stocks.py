import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from apps.stocks.models import Stock, StockPrice, StockWatchlist


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
def stock_price(stock: Stock) -> StockPrice:
    return StockPrice.objects.create(
        stock=stock,
        price=Decimal("150.00"),
        volume=1000000,
        high=Decimal("155.00"),
        low=Decimal("145.00"),
        open_price=Decimal("148.00"),
        close_price=Decimal("150.00"),
        timestamp=timezone.now() - timedelta(days=1),
    )


@pytest.fixture
def watchlist_item(user: User, stock: Stock) -> StockWatchlist:
    return StockWatchlist.objects.create(
        user=user,
        stock=stock,
    )


def test_list_stocks_authenticated(authenticated_client: APIClient, stock: Stock, stock_price: StockPrice):
    url = reverse("stocks:stock-list")
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["symbol"] == stock.symbol
    assert response.data['results'][0]["name"] == stock.name
    assert response.data['results'][0]["type"] == stock.type
    assert "latest_price" in response.data['results'][0]


def test_list_stocks_unauthenticated(api_client: APIClient):
    url = reverse("stocks:stock-list")
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_retrieve_stock_by_symbol(authenticated_client: APIClient, stock: Stock, stock_price: StockPrice):
    url = reverse("stocks:stock-detail", kwargs={"symbol": stock.symbol})
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["symbol"] == stock.symbol
    assert response.data["name"] == stock.name
    assert response.data["type"] == stock.type
    assert "latest_price" in response.data


def test_retrieve_stock_case_insensitive(authenticated_client: APIClient, stock: Stock):
    url = reverse("stocks:stock-detail", kwargs={"symbol": stock.symbol.lower()})
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["symbol"] == stock.symbol


def test_retrieve_nonexistent_stock(authenticated_client: APIClient):
    url = reverse("stocks:stock-detail", kwargs={"symbol": "NONEXISTENT"})
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_retrieve_stock_unauthenticated(api_client: APIClient, stock: Stock):
    url = reverse("stocks:stock-detail", kwargs={"symbol": stock.symbol})
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_stock_price_history(authenticated_client: APIClient, stock: Stock, stock_price: StockPrice):
    url = reverse("stocks:stock-prices", kwargs={"symbol": stock.symbol})
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["stock"] == stock.id
    assert Decimal(response.data['results'][0]["price"]) == stock_price.price
    assert response.data['results'][0]["volume"] == stock_price.volume
    assert Decimal(response.data['results'][0]["high"]) == stock_price.high
    assert Decimal(response.data['results'][0]["low"]) == stock_price.low


def test_stock_price_history_nonexistent_stock(authenticated_client: APIClient):
    url = reverse("stocks:stock-prices", kwargs={"symbol": "NONEXISTENT"})
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_stock_price_history_unauthenticated(api_client: APIClient, stock: Stock):
    url = reverse("stocks:stock-prices", kwargs={"symbol": stock.symbol})
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_watchlist(authenticated_client: APIClient, watchlist_item: StockWatchlist):
    url = reverse("stocks:watchlist")
    
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data['count'] == 1
    assert len(response.data['results']) == 1
    assert response.data['results'][0]["id"] == watchlist_item.id
    assert response.data['results'][0]["stock"] == watchlist_item.stock.id


def test_list_watchlist_unauthenticated(api_client: APIClient):
    url = reverse("stocks:watchlist")
    
    response = api_client.get(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_add_stock_to_watchlist(authenticated_client: APIClient, stock: Stock):
    url = reverse("stocks:watchlist")
    payload = {
        "stock": stock.id,
    }
    
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert StockWatchlist.objects.count() == 1
    watchlist_item = StockWatchlist.objects.first()
    assert watchlist_item.stock.id == stock.id


def test_add_nonexistent_stock_to_watchlist(authenticated_client: APIClient):
    url = reverse("stocks:watchlist")
    payload = {
        "stock": 999,  # Non-existent stock ID
    }
    
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "stock" in response.data


def test_add_duplicate_stock_to_watchlist(authenticated_client: APIClient, watchlist_item: StockWatchlist):
    url = reverse("stocks:watchlist")
    payload = {
        "stock": watchlist_item.stock.id,
    }
    
    response = authenticated_client.post(url, payload, format="json")
    
    # The implementation allows duplicate watchlist items, so we expect a 201 Created
    assert response.status_code == status.HTTP_201_CREATED


def test_add_stock_to_watchlist_unauthenticated(api_client: APIClient, stock: Stock):
    url = reverse("stocks:watchlist")
    payload = {
        "stock": stock.id,
    }
    
    response = api_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_remove_stock_from_watchlist(authenticated_client: APIClient, watchlist_item: StockWatchlist):
    url = reverse("stocks:watchlist-detail", kwargs={"pk": watchlist_item.id})
    
    response = authenticated_client.delete(url)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert StockWatchlist.objects.count() == 0


def test_remove_nonexistent_watchlist_item(authenticated_client: APIClient):
    url = reverse("stocks:watchlist-detail", kwargs={"pk": 999})
    
    response = authenticated_client.delete(url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_stock_from_watchlist_unauthenticated(api_client: APIClient, watchlist_item: StockWatchlist):
    url = reverse("stocks:watchlist-detail", kwargs={"pk": watchlist_item.id})
    
    response = api_client.delete(url)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert StockWatchlist.objects.count() == 1


def test_remove_another_users_watchlist_item(authenticated_client: APIClient):
    # Create another user
    another_user = User.objects.create_user(
        username="anotheruser",
        email="another@example.com",
        password="testpass123",
    )
    
    # Create a stock
    another_stock = Stock.objects.create(
        symbol="MSFT",
        name="Microsoft Corporation",
        type="Technology",
        is_active=True,
    )
    
    # Add stock to another user's watchlist
    another_watchlist_item = StockWatchlist.objects.create(
        user=another_user,
        stock=another_stock,
    )
    
    # Try to delete it with the authenticated client (which is authenticated as testuser)
    url = reverse("stocks:watchlist-detail", kwargs={"pk": another_watchlist_item.id})
    
    response = authenticated_client.delete(url)
    
    # Should return 404 because the watchlist item doesn't belong to the authenticated user
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert StockWatchlist.objects.count() == 1
