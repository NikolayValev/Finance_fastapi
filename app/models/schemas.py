from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AssetPrice(BaseModel):
    symbol: str
    price: float
    currency: str
    source: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EconomicIndicator(BaseModel):
    indicator: str
    value: float
    country: str
    date: str
    source: str
    unit: Optional[str] = None

class BondGroup(BaseModel):
    security_type: str
    total_issuance: float
    average_yield: float
    auction_count: int

class BondAggregationResponse(BaseModel):
    period: str
    currency: str = "USD"
    data: List[BondGroup]

class YieldCurvePoint(BaseModel):
    maturity: str
    rate: float

class TrendData(BaseModel):
    date: str
    total_issuance: float

class SpreadAnalysis(BaseModel):
    spread_value: float
    is_inverted: bool
    date: str

class LiquidityPoint(BaseModel):
    date: str
    balance_billion: float

class InterestRatePoint(BaseModel):
    date: str
    avg_rate: float

class DebtPoint(BaseModel):
    date: str
    total_debt: float
    daily_change: float
