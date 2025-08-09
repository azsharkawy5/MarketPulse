from django.contrib import admin
from django.urls import path, include
from MarketPulse.health_check import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.stocks.urls")),
    path("api/v1/", include("apps.alerts.urls")),
    path("health/", health, name="health"),
]
