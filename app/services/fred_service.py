import httpx
from app.models.schemas import EconomicIndicator
from app.config import settings
from datetime import datetime

from fastapi_cache.decorator import cache

class FredService:
    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    @cache(expire=86400)
    async def get_series_data(self, series_id: str) -> EconomicIndicator:
        if not settings.FRED_API_KEY:
            raise ValueError("FRED_API_KEY not set")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.BASE_URL,
                params={
                    "series_id": series_id,
                    "api_key": settings.FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data["observations"]:
                raise ValueError(f"No data found for series {series_id}")
                
            latest = data["observations"][0]
            
            # Map common series IDs to readable names
            series_names = {
                "CPIAUCSL": "CPI (Consumer Price Index)",
                "UNRATE": "Unemployment Rate",
                "FEDFUNDS": "Federal Funds Rate",
                "DGS10": "10-Year Treasury Constant Maturity Rate"
            }
            
            return EconomicIndicator(
                indicator=series_names.get(series_id, series_id),
                value=float(latest["value"]),
                country="United States",
                date=latest["date"],
                source="FRED",
                unit="Index/Percent" # Simplified, ideally would fetch series info to get unit
            )
