import httpx
from app.models.schemas import AssetPrice
from datetime import datetime

from fastapi_cache.decorator import cache

class FrankfurterService:
    BASE_URL = "https://api.frankfurter.app"

    @cache(expire=3600)
    async def get_exchange_rate(self, from_currency: str, to_currency: str = "USD") -> AssetPrice:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/latest",
                params={"from": from_currency.upper(), "to": to_currency.upper()}
            )
            response.raise_for_status()
            data = response.json()
            
            rate = data["rates"][to_currency.upper()]
            
            return AssetPrice(
                symbol=f"{from_currency.upper()}/{to_currency.upper()}",
                price=rate,
                currency=to_currency.upper(),
                source="Frankfurter",
                timestamp=data["date"] # Frankfurter returns date, not timestamp
            )
