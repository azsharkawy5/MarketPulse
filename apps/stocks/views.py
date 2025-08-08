from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from .models import Stock, StockPrice, StockWatchlist
from .serializers import (
    StockPriceSerializer,
    StockWatchlistSerializer,
    StockWithLatestPriceSerializer,
)


class StockListView(generics.ListAPIView):
    """
    View to list all stocks with their latest prices.
    """

    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockWithLatestPriceSerializer
    permission_classes = [permissions.IsAuthenticated]


class StockDetailView(generics.RetrieveAPIView):
    """
    View to get detailed information about a specific stock.
    """

    queryset = Stock.objects.filter(is_active=True)
    serializer_class = StockWithLatestPriceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        symbol = self.kwargs.get("symbol").upper()
        return get_object_or_404(Stock, symbol=symbol, is_active=True)


class StockPriceHistoryView(generics.ListAPIView):
    """
    View to get historical price data for a stock.
    """

    serializer_class = StockPriceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        symbol = self.kwargs.get("symbol")
        stock = get_object_or_404(Stock, symbol=symbol.upper(), is_active=True)
        return StockPrice.objects.filter(stock=stock).order_by("-timestamp")[:100]


class StockWatchlistView(generics.ListCreateAPIView):
    """
    View to manage user's stock watchlist.
    """

    serializer_class = StockWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StockWatchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StockWatchlistDetailView(generics.DestroyAPIView):
    """
    View to remove a stock from user's watchlist.
    """

    serializer_class = StockWatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StockWatchlist.objects.filter(user=self.request.user)
