import httpx
from app.models.schemas import EconomicIndicator
from datetime import datetime

from fastapi_cache.decorator import cache

class TreasuryService:
    BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

    @cache(expire=86400)
    async def get_total_debt(self) -> EconomicIndicator:
        endpoint = "/v2/accounting/od/debt_to_penny"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}{endpoint}",
                params={"sort": "-record_date", "page[size]": 1}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data["data"]:
                raise ValueError("No debt data found")
                
            latest_record = data["data"][0]
            
            return EconomicIndicator(
                indicator="Total Public Debt Outstanding",
                value=float(latest_record["tot_pub_debt_out_amt"]),
                country="United States",
                date=latest_record["record_date"],
                source="US Treasury",
                unit="USD"
            )
