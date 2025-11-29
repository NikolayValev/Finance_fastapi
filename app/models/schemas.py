from pydantic import BaseModel
from typing import Optional, Dict, Any

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
