from django.core.management.base import BaseCommand
from apps.stocks.models import Stock


class Command(BaseCommand):
    help = "Seed initial stock data"

    def handle(self, *args, **options):
        stocks_data = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "type": "Technology",
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "type": "Technology",
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "type": "Technology",
            },
            {
                "symbol": "AMZN",
                "name": "Amazon.com Inc.",
                "type": "Consumer Cyclical",
            },
            {
                "symbol": "TSLA",
                "name": "Tesla Inc.",
                "type": "Consumer Cyclical",
            },
            {
                "symbol": "META",
                "name": "Meta Platforms Inc.",
                "type": "Technology",
            },
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "type": "Technology",
            },
            {
                "symbol": "NFLX",
                "name": "Netflix Inc.",
                "type": "Communication Services",
            },
            {
                "symbol": "AMD",
                "name": "Advanced Micro Devices Inc.",
                "type": "Technology",
            },
            {
                "symbol": "INTC",
                "name": "Intel Corporation",
                "type": "Technology",
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
