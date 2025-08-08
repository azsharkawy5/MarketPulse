from django.db import models
from django.conf import settings

class Stock(models.Model):
    """
    Model to store stock information.
    """
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StockPrice(models.Model):
    """
    Model to store historical stock price data.
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class StockWatchlist(models.Model):
    """
    Model to store user's watchlist of stocks.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlists')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='watchlists')
    added_at = models.DateTimeField(auto_now_add=True)
