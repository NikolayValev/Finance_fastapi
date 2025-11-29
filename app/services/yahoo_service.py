import yfinance as yf
from app.models.schemas import AssetPrice
from datetime import datetime

from fastapi_cache.decorator import cache

class YahooFinanceService:
    @cache(expire=60)
    def get_stock_price(self, ticker: str) -> AssetPrice:
        ticker_obj = yf.Ticker(ticker)
        # fast_info is often faster than history(period="1d")
        price = ticker_obj.fast_info.last_price
        currency = ticker_obj.fast_info.currency
        
        return AssetPrice(
            symbol=ticker.upper(),
            price=price,
            currency=currency,
            source="Yahoo Finance",
            timestamp=datetime.now().isoformat()
        )
