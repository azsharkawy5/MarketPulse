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
        url = f"{settings.STOCK_API_BASE_URL}"
        params = {
            "symbol": symbol,
            "apikey": settings.STOCK_API_KEY,
        }

        response = requests.get(url, params=params, timeout=10)
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
                "name": data.get("name", symbol),
                "sector": data.get("sector", ""),
                "industry": data.get("industry", ""),
            },
        )

        # Update stock info if not newly created
        if not created:
            stock.name = data.get("name", stock.name)
            stock.sector = data.get("sector", stock.sector)
            stock.industry = data.get("industry", stock.industry)
            stock.save()

        # Create price record
        price_data = {
            "stock": stock,
            "price": Decimal(str(data.get("close", 0))),
            "volume": int(data.get("volume", 0)),
            "high": Decimal(str(data.get("high", 0))),
            "low": Decimal(str(data.get("low", 0))),
            "open_price": Decimal(str(data.get("open", 0))),
            "close_price": Decimal(str(data.get("close", 0))),
            "timestamp": timezone.now(),
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
