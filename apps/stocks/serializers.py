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
            "sector",
            "industry",
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
