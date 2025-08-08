from django.core.management.base import BaseCommand
from apps.stocks.models import Stock


class Command(BaseCommand):
    help = "Seed initial stock data"

    def handle(self, *args, **options):
        stocks_data = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "sector": "Technology",
                "industry": "Internet Content & Information",
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "sector": "Technology",
                "industry": "Software - Infrastructure",
            },
            {
                "symbol": "AMZN",
                "name": "Amazon.com Inc.",
                "sector": "Consumer Cyclical",
                "industry": "Internet Retail",
            },
            {
                "symbol": "TSLA",
                "name": "Tesla Inc.",
                "sector": "Consumer Cyclical",
                "industry": "Auto Manufacturers",
            },
            {
                "symbol": "META",
                "name": "Meta Platforms Inc.",
                "sector": "Technology",
                "industry": "Internet Content & Information",
            },
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "sector": "Technology",
                "industry": "Semiconductors",
            },
            {
                "symbol": "NFLX",
                "name": "Netflix Inc.",
                "sector": "Communication Services",
                "industry": "Entertainment",
            },
            {
                "symbol": "AMD",
                "name": "Advanced Micro Devices Inc.",
                "sector": "Technology",
                "industry": "Semiconductors",
            },
            {
                "symbol": "INTC",
                "name": "Intel Corporation",
                "sector": "Technology",
                "industry": "Semiconductors",
            },
        ]

        created_count = 0
        updated_count = 0

        for stock_data in stocks_data:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data["symbol"], defaults=stock_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created stock: {stock.symbol} - {stock.name}")
                )
            else:
                # Update existing stock with new data
                for key, value in stock_data.items():
                    setattr(stock, key, value)
                stock.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated stock: {stock.symbol} - {stock.name}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded stock data. Created: {created_count}, Updated: {updated_count}"
            )
        )
