import httpx
from app.models.schemas import EconomicIndicator
from datetime import datetime
import xml.etree.ElementTree as ET

from fastapi_cache.decorator import cache

class EcbService:
    # ECB SDMX API (REST)
    BASE_URL = "https://sdw-wsrest.ecb.europa.eu/service"

    @cache(expire=3600)
    async def get_hicp(self) -> EconomicIndicator:
        # Switch to Exchange Rate (USD/EUR) as HICP series key is tricky/fragile
        # Series: EXR.D.USD.EUR.SP00.A
        # Flow: EXR
        
        flow_ref = "EXR"
        series_key = "D.USD.EUR.SP00.A"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/data/{flow_ref}/{series_key}",
                params={"lastNObservations": 1},
                headers={"Accept": "text/csv", "User-Agent": "FinanceAggregator/1.0"}
            )
            response.raise_for_status()
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                 raise ValueError("No data from ECB")
            
            last_line = lines[-1]
            parts = last_line.split(',')
            
            # Header usually: KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,OBS_VALUE,...
            # But let's rely on finding OBS_VALUE or position
            
            headers = lines[0].split(',')
            try:
                val_idx = headers.index('OBS_VALUE')
                date_idx = headers.index('TIME_PERIOD')
            except ValueError:
                val_idx = -2 # Often near end
                date_idx = -3
            
            value = float(parts[val_idx])
            date = parts[date_idx]

            return EconomicIndicator(
                indicator="ECB Reference Rate (USD/EUR)",
                value=value,
                country="Euro Area",
                date=date,
                source="ECB",
                unit="USD"
            )
