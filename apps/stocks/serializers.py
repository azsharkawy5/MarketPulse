from rest_framework import serializers
from .models import Stock, StockPrice, StockWatchlist


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer for stock information.
    """

    class Meta:
        model = Stock
        fields = [
            "id",
            "symbol",
            "name",
            "type",
            "is_active",
            "created_at",
        ]


class StockPriceSerializer(serializers.ModelSerializer):
    """
    Serializer for stock price data.
    """

    stock_symbol = serializers.CharField(source="stock.symbol", read_only=True)
    stock_name = serializers.CharField(source="stock.name", read_only=True)

    class Meta:
        model = StockPrice
        fields = [
            "id",
            "stock",
            "stock_symbol",
            "stock_name",
            "price",
            "volume",
            "high",
            "low",
            "open_price",
            "close_price",
            "timestamp",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class StockWatchlistSerializer(serializers.ModelSerializer):
    """
    Serializer for user's stock watchlist.
    """

    stock_details = StockSerializer(source="stock", read_only=True)

    class Meta:
        model = StockWatchlist
        fields = ["id", "stock", "stock_details", "added_at"]
        read_only_fields = ["added_at"]


class StockWithLatestPriceSerializer(serializers.ModelSerializer):
    """
    Serializer for stock with its latest price information.
    """

    latest_price = serializers.SerializerMethodField()
    price_change = serializers.SerializerMethodField()
    price_change_percent = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = [
            "id",
            "symbol",
            "name",
            "type",
            "latest_price",
            "price_change",
            "price_change_percent",
        ]

    def get_latest_price(self, obj):
        latest_price = obj.prices.first()
        if latest_price:
            return {
                "price": latest_price.price,
                "volume": latest_price.volume,
                "high": latest_price.high,
                "low": latest_price.low,
                "open": latest_price.open_price,
                "close": latest_price.close_price,
                "timestamp": latest_price.timestamp,
            }
        return None

    def get_price_change(self, obj):
        latest_price = obj.prices.first()
        if latest_price:
            return float(latest_price.close_price - latest_price.open_price)
        return 0

    def get_price_change_percent(self, obj):
        latest_price = obj.prices.first()
        if latest_price and latest_price.open_price > 0:
            change = latest_price.close_price - latest_price.open_price
            return float((change / latest_price.open_price) * 100)
        return 0
