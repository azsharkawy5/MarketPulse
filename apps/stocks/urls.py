from django.urls import path
from . import views

app_name = "stocks"

urlpatterns = [
    path("stocks/", views.StockListView.as_view(), name="stock-list"),
    path("stocks/<str:symbol>/", views.StockDetailView.as_view(), name="stock-detail"),
    path(
        "stocks/<str:symbol>/prices/",
        views.StockPriceHistoryView.as_view(),
        name="stock-prices",
    ),
    path("watchlist/", views.StockWatchlistView.as_view(), name="watchlist"),
    path(
        "watchlist/<int:pk>/",
        views.StockWatchlistDetailView.as_view(),
        name="watchlist-detail",
    ),
]
