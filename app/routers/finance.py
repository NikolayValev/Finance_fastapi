from fastapi import APIRouter, HTTPException
from app.services.yahoo_service import YahooFinanceService
from app.services.coingecko_service import CoinGeckoService
from app.models.schemas import AssetPrice

router = APIRouter()
yahoo_service = YahooFinanceService()
coingecko_service = CoinGeckoService()

@router.get("/stocks/{ticker}", response_model=AssetPrice)
async def get_stock(ticker: str):
    try:
        return await yahoo_service.get_stock_price(ticker)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/crypto/{coin_id}", response_model=AssetPrice)
async def get_crypto(coin_id: str, currency: str = "usd"):
    try:
        return await coingecko_service.get_coin_price(coin_id, currency)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
