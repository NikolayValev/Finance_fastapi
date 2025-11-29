from fastapi import APIRouter, HTTPException
from app.services.frankfurter_service import FrankfurterService
from app.services.worldbank_service import WorldBankService
from app.services.treasury_service import TreasuryService
from app.models.schemas import AssetPrice, EconomicIndicator

from app.services.fred_service import FredService
from app.services.ecb_service import EcbService

router = APIRouter()
frankfurter_service = FrankfurterService()
worldbank_service = WorldBankService()
treasury_service = TreasuryService()
fred_service = FredService()
ecb_service = EcbService()

@router.get("/forex/{from_currency}", response_model=AssetPrice)
async def get_forex(from_currency: str, to_currency: str = "USD"):
    try:
        return await frankfurter_service.get_exchange_rate(from_currency, to_currency)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/economy/gdp/{country_code}", response_model=EconomicIndicator)
async def get_gdp(country_code: str):
    try:
        return await worldbank_service.get_gdp(country_code)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/treasury/debt", response_model=EconomicIndicator)
async def get_us_debt():
    try:
        return await treasury_service.get_total_debt()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/fred/{series_id}", response_model=EconomicIndicator)
async def get_fred_data(series_id: str):
    try:
        return await fred_service.get_series_data(series_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/ecb/hicp", response_model=EconomicIndicator)
async def get_ecb_hicp():
    try:
        return await ecb_service.get_hicp()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"DEBUG ERROR: {str(e)}")
