import httpx
from app.models.schemas import EconomicIndicator
from datetime import datetime

from fastapi_cache.decorator import cache

class WorldBankService:
    BASE_URL = "https://api.worldbank.org/v2"

    @cache(expire=86400)
    async def get_gdp(self, country_code: str) -> EconomicIndicator:
        # Indicator for GDP (current US$): NY.GDP.MKTP.CD
        indicator_code = "NY.GDP.MKTP.CD"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/country/{country_code}/indicator/{indicator_code}",
                params={"format": "json", "per_page": 1}
            )
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2 or not data[1]:
                raise ValueError(f"No data found for country {country_code}")
                
            latest_data = data[1][0]
            
            return EconomicIndicator(
                indicator="GDP",
                value=latest_data["value"],
                country=latest_data["country"]["value"],
                date=latest_data["date"],
                source="World Bank",
                unit="USD"
            )
