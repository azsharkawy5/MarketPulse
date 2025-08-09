import logging
import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from celery import shared_task
from .models import Stock, StockPrice

logger = logging.getLogger(__name__)


@shared_task
def fetch_single_stock_data(symbol):
    """
    Fetch data for a single stock symbol.
    """
    if not settings.STOCK_API_KEY:
        logger.error("Stock API key not configured")
        return

    try:
        url = f"{settings.STOCK_API_BASE_URL}{settings.STOCK_API_ENDPOINT}?apikey={settings.STOCK_API_KEY}&symbol={symbol}&interval={settings.STOCK_API_INTERVAL}&format={settings.STOCK_API_FORMAT}&outputsize={settings.STOCK_API_SIZE}&type={settings.STOCK_TYPE}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if "status" in data and data["status"] == "error":
            logger.error(
                f"API error for {symbol}: {data.get('message', 'Unknown error')}"
            )
            return

        # Extract stock information
        stock, created = Stock.objects.get_or_create(
            symbol=symbol.upper(),
            defaults={
                "symbol": data.get("meta", {}).get("symbol", symbol),
                "name": data.get("meta", {}).get("name", symbol),
                "type": data.get("meta", {}).get("type", "N/A"),
            },
        )

        # Update stock info if not newly created
        if not created:
            stock.symbol = data.get("meta", {}).get("symbol", stock.symbol)
            stock.name = data.get("meta", {}).get("name", stock.name)
            stock.type = data.get("meta", {}).get("type", stock.type)
            stock.save()

        # Create price record
        price_data = {
            "stock": stock,
            "price": Decimal(str(data.get("values", [{}])[0].get("close", 0))),
            "volume": int(data.get("values", [{}])[0].get("volume", 0)),
            "high": Decimal(str(data.get("values", [{}])[0].get("high", 0))),
            "low": Decimal(str(data.get("values", [{}])[0].get("low", 0))),
            "open_price": Decimal(str(data.get("values", [{}])[0].get("open", 0))),
            "close_price": Decimal(str(data.get("values", [{}])[0].get("close", 0))),
            "timestamp": timezone.datetime.strptime(
                data.get("values", [{}])[0].get("datetime", ""),
                "%Y-%m-%d %H:%M:%S",
            ),
            "created_at": timezone.now(),
        }

        # Check if we already have a price record for this timestamp
        existing_price = StockPrice.objects.filter(
            stock=stock, timestamp__date=price_data["timestamp"].date()
        ).first()

        if existing_price:
            # Update existing record
            for key, value in price_data.items():
                if key != "stock":
                    setattr(existing_price, key, value)
            existing_price.save()
        else:
            # Create new record
            StockPrice.objects.create(**price_data)

        logger.info(f"Successfully fetched data for {symbol}")

    except requests.RequestException as e:
        logger.error(f"Request error fetching data for {symbol}: {e}")
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")


@shared_task
def fetch_stock_data_batch():
    """
    Fetch data for a batch of popular stocks.
    """
    # Predefined list of popular stocks for mvp
    # TODO In a real application, this could be dynamic or fetched from a database or config
    popular_stocks = [
        "AAPL",
        "GOOGL",
        "MSFT",
        "AMZN",
        "TSLA",
        "META",
        "NVDA",
        "NFLX",
        "AMD",
        "INTC",
    ]

    for symbol in popular_stocks:
        try:
            fetch_single_stock_data.delay(symbol)
        except Exception as e:
            logger.error(f"Error scheduling fetch for {symbol}: {e}")


@shared_task
def cleanup_old_price_data():
    """
    Clean up old price data to prevent database bloat.
    Keep only last 30 days of data.
    """
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=30)
    deleted_count = StockPrice.objects.filter(timestamp__lt=cutoff_date).delete()[0]

    logger.info(f"Cleaned up {deleted_count} old price records")
