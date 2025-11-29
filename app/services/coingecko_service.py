import httpx
from app.models.schemas import AssetPrice
from datetime import datetime

from fastapi_cache.decorator import cache

class CoinGeckoService:
    BASE_URL = "https://api.coingecko.com/api/v3"

    @cache(expire=60)
    async def get_coin_price(self, coin_id: str, currency: str = "usd") -> AssetPrice:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/simple/price",
                params={"ids": coin_id, "vs_currencies": currency}
            )
            response.raise_for_status()
            data = response.json()
            
            if coin_id not in data:
                raise ValueError(f"Coin {coin_id} not found")
                
            price = data[coin_id][currency]
            
            return AssetPrice(
                symbol=coin_id.upper(),
                price=price,
                currency=currency.upper(),
                source="CoinGecko",
                timestamp=datetime.now().isoformat()
            )
