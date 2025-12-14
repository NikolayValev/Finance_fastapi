from fastapi import APIRouter, HTTPException
from app.services.frankfurter_service import FrankfurterService
from app.services.worldbank_service import WorldBankService
from app.services.treasury_service import TreasuryService
from app.models.schemas import (
    AssetPrice, 
    EconomicIndicator,
    YieldCurvePoint,
    TrendData,
    SpreadAnalysis,
    LiquidityPoint,
    InterestRatePoint,
    DebtPoint
)
from typing import List

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

@router.get("/treasury/yield-curve", response_model=List[YieldCurvePoint])
async def get_yield_curve():
    """
    Get the most recent Treasury yield curve data.
    Returns maturity/rate pairs suitable for line chart visualization.
    """
    try:
        return await treasury_service.get_daily_yield_curve()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/treasury/issuance-trend", response_model=List[TrendData])
async def get_issuance_trend(months: int = 12):
    """
    Get monthly bond issuance trends for the specified period.
    
    Args:
        months: Number of months to look back (default: 12)
    """
    try:
        return await treasury_service.get_issuance_trend(months_back=months)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/treasury/spread-10-2", response_model=SpreadAnalysis)
async def get_spread_analysis():
    """
    Get the 10-Year minus 2-Year Treasury spread analysis.
    An inverted spread (negative value) is often considered a recession indicator.
    """
    try:
        return await treasury_service.get_10_2_spread()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/treasury/tga-liquidity", response_model=List[LiquidityPoint])
async def get_tga_liquidity(days: int = 90):
    """
    Get Treasury General Account (TGA) balance time-series - the "Shadow QE" indicator.
    A dropping TGA balance increases market liquidity (bullish/QE-like effect).
    
    Args:
        days: Number of days to look back (default: 90)
    """
    try:
        return await treasury_service.get_tga_liquidity(days_back=days)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/treasury/debt-cost-trend", response_model=List[InterestRatePoint])
async def get_debt_cost_trend(years: int = 5):
    """
    Get the average interest rate paid on all outstanding debt over time.
    Shows if the "cost of carry" is peaking or dropping as rates change.
    
    Args:
        years: Number of years to look back (default: 5)
    """
    try:
        return await treasury_service.get_debt_cost_trend(years_back=years)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/treasury/debt-history", response_model=List[DebtPoint])
async def get_debt_history(days: int = 365):
    """
    Get total public debt outstanding with daily changes.
    Visualizes the acceleration of debt issuance.
    
    Args:
        days: Number of days to look back (default: 365)
    """
    try:
        return await treasury_service.get_debt_history(days_back=days)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
