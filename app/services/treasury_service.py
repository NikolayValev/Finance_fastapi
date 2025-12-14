import httpx
from app.models.schemas import (
    EconomicIndicator, 
    BondAggregationResponse, 
    BondGroup,
    YieldCurvePoint,
    TrendData,
    SpreadAnalysis,
    LiquidityPoint,
    InterestRatePoint,
    DebtPoint
)
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Optional

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

    @cache(expire=86400)  # Cache for 24 hours
    async def get_bond_issuance_summary(self, months_back: int = 6) -> BondAggregationResponse:
        endpoint = "/v1/accounting/od/auctions_query"
        
        # 1. Calculate Date Filter (YYYY-MM-DD)
        start_date = (datetime.now() - timedelta(days=30 * months_back)).date()
        date_filter = f"auction_date:gte:{start_date}"

        # 2. Prepare Aggregation Containers
        # Structure: { "Bill": { "total_amt": 0.0, "yield_sum": 0.0, "count": 0 } }
        agg_data = defaultdict(lambda: {"total_amt": 0.0, "yield_sum": 0.0, "count": 0})

        async with httpx.AsyncClient() as client:
            page = 1
            has_more = True
            
            while has_more:
                params = {
                    "filter": date_filter,
                    "page[size]": 100,  # Maximize to reduce requests
                    "page[number]": page,
                    "format": "json"
                }
                
                response = await client.get(f"{self.BASE_URL}{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("data", [])

                if not results:
                    has_more = False
                    break

                # 3. Process & Aggregate Current Page
                for item in results:
                    sec_type = item.get("security_type", "Unknown")
                    amt_str = item.get("offering_amount")
                    yield_str = item.get("high_yield")  # Interest rate

                    if amt_str and yield_str:
                        try:
                            agg_data[sec_type]["total_amt"] += float(amt_str)
                            agg_data[sec_type]["yield_sum"] += float(yield_str)
                            agg_data[sec_type]["count"] += 1
                        except ValueError:
                            continue  # Skip malformed rows

                # Check pagination metadata to see if we need another loop
                meta = data.get("meta", {})
                total_pages = meta.get("total-pages", 0)
                
                if page >= total_pages:
                    has_more = False
                else:
                    page += 1

        # 4. Format Output
        summary_list = []
        for sec_type, stats in agg_data.items():
            if stats["count"] > 0:
                avg_yield = stats["yield_sum"] / stats["count"]
                summary_list.append(BondGroup(
                    security_type=sec_type,
                    total_issuance=round(stats["total_amt"], 2),
                    average_yield=round(avg_yield, 4),
                    auction_count=stats["count"]
                ))

        return BondAggregationResponse(
            period=f"Last {months_back} Months",
            data=summary_list
        )

    @cache(expire=86400)  # Cache for 24 hours
    async def get_daily_yield_curve(self) -> List[YieldCurvePoint]:
        """
        Fetch the most recent Treasury yield curve data and transform it 
        into a list of maturity/rate pairs suitable for line charts.
        
        Returns:
            List[YieldCurvePoint]: List of yield curve points
        """
        endpoint = "/v2/accounting/od/daily_treasury_yield_curve"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}{endpoint}",
                params={"sort": "-record_date", "page[size]": 1}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                raise ValueError("No yield curve data found")
            
            latest_record = data["data"][0]
            
            # Map Treasury field names to human-readable maturities
            maturity_mapping = [
                ("BC_1MONTH", "1 Month"),
                ("BC_3MONTH", "3 Month"),
                ("BC_1YEAR", "1 Year"),
                ("BC_2YEAR", "2 Year"),
                ("BC_5YEAR", "5 Year"),
                ("BC_10YEAR", "10 Year"),
                ("BC_20YEAR", "20 Year"),
                ("BC_30YEAR", "30 Year")
            ]
            
            yield_curve = []
            for field_name, maturity_label in maturity_mapping:
                rate_str = latest_record.get(field_name)
                if rate_str is not None:
                    try:
                        rate = float(rate_str)
                        yield_curve.append(YieldCurvePoint(
                            maturity=maturity_label,
                            rate=rate
                        ))
                    except (ValueError, TypeError):
                        # Skip invalid data points
                        continue
            
            return yield_curve

    @cache(expire=86400)  # Cache for 24 hours
    async def get_issuance_trend(self, months_back: int = 12) -> List[TrendData]:
        """
        Fetch bond issuance data for the last N months and aggregate by month.
        
        Args:
            months_back: Number of months to look back (default: 12)
            
        Returns:
            List[TrendData]: Monthly issuance totals
        """
        endpoint = "/v1/accounting/od/auctions_query"
        
        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=30 * months_back)).date()
        date_filter = f"auction_date:gte:{start_date}"
        
        # Aggregation by year-month
        monthly_totals = defaultdict(float)
        
        async with httpx.AsyncClient() as client:
            page = 1
            has_more = True
            
            while has_more:
                params = {
                    "filter": date_filter,
                    "page[size]": 100,
                    "page[number]": page,
                    "format": "json"
                }
                
                response = await client.get(f"{self.BASE_URL}{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("data", [])
                
                if not results:
                    has_more = False
                    break
                
                # Aggregate by year-month
                for item in results:
                    auction_date = item.get("auction_date")
                    amt_str = item.get("offering_amount")
                    
                    if auction_date and amt_str:
                        try:
                            # Extract year-month (e.g., "2023-11")
                            year_month = auction_date[:7]
                            amount = float(amt_str)
                            monthly_totals[year_month] += amount
                        except (ValueError, IndexError):
                            continue
                
                # Check pagination
                meta = data.get("meta", {})
                total_pages = meta.get("total-pages", 0)
                
                if page >= total_pages:
                    has_more = False
                else:
                    page += 1
        
        # Format output and sort by date
        trend_data = [
            TrendData(date=month, total_issuance=round(total, 2))
            for month, total in monthly_totals.items()
        ]
        trend_data.sort(key=lambda x: x.date)
        
        return trend_data

    @cache(expire=86400)  # Cache for 24 hours
    async def get_10_2_spread(self) -> SpreadAnalysis:
        """
        Calculate the 10-Year minus 2-Year Treasury spread.
        An inverted spread (negative value) is often considered a recession indicator.
        
        Returns:
            SpreadAnalysis: Spread value, inversion status, and date
        """
        endpoint = "/v2/accounting/od/daily_treasury_yield_curve"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}{endpoint}",
                params={"sort": "-record_date", "page[size]": 1}
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                raise ValueError("No yield curve data found")
            
            latest_record = data["data"][0]
            record_date = latest_record.get("record_date", "Unknown")
            
            # Extract 10-year and 2-year rates
            rate_10y_str = latest_record.get("BC_10YEAR")
            rate_2y_str = latest_record.get("BC_2YEAR")
            
            if rate_10y_str is None or rate_2y_str is None:
                raise ValueError("Missing 10-year or 2-year rate data")
            
            try:
                rate_10y = float(rate_10y_str)
                rate_2y = float(rate_2y_str)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid rate data: {e}")
            
            # Calculate spread
            spread_value = rate_10y - rate_2y
            is_inverted = spread_value < 0
            
            return SpreadAnalysis(
                spread_value=round(spread_value, 4),
                is_inverted=is_inverted,
                date=record_date
            )

    @cache(expire=86400)  # Cache for 24 hours
    async def get_tga_liquidity(self, days_back: int = 90) -> List[LiquidityPoint]:
        """
        Track Treasury General Account (TGA) balance - the "Shadow QE" indicator.
        A dropping TGA balance increases market liquidity (bullish/QE-like effect).
        
        Args:
            days_back: Number of days to look back (default: 90)
            
        Returns:
            List[LiquidityPoint]: Time-series of TGA balances in billions
        """
        endpoint = "/v1/accounting/dts/dts_table_1"
        
        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=days_back)).date()
        date_filter = f"record_date:gte:{start_date}"
        
        # Additional filters for TGA data
        filters = [
            date_filter,
            "account_type:eq:Treasury General Account (TGA)",
            "item:eq:Closing Balance"
        ]
        filter_string = ",".join(filters)
        
        liquidity_data = []
        
        async with httpx.AsyncClient() as client:
            page = 1
            has_more = True
            
            while has_more:
                params = {
                    "filter": filter_string,
                    "sort": "record_date",
                    "page[size]": 100,
                    "page[number]": page,
                    "format": "json"
                }
                
                response = await client.get(f"{self.BASE_URL}{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("data", [])
                
                if not results:
                    has_more = False
                    break
                
                # Process each record
                for item in results:
                    record_date = item.get("record_date")
                    close_balance_str = item.get("close_today_bal")
                    
                    if record_date and close_balance_str:
                        try:
                            # Remove commas and convert to float, then to billions
                            balance = float(close_balance_str.replace(",", ""))
                            balance_billion = balance / 1_000_000_000
                            
                            liquidity_data.append(LiquidityPoint(
                                date=record_date,
                                balance_billion=round(balance_billion, 2)
                            ))
                        except (ValueError, AttributeError):
                            continue
                
                # Check pagination
                meta = data.get("meta", {})
                total_pages = meta.get("total-pages", 0)
                
                if page >= total_pages:
                    has_more = False
                else:
                    page += 1
        
        # Sort by date
        liquidity_data.sort(key=lambda x: x.date)
        
        return liquidity_data

    @cache(expire=86400)  # Cache for 24 hours
    async def get_debt_cost_trend(self, years_back: int = 5) -> List[InterestRatePoint]:
        """
        Track the average interest rate paid on all outstanding debt.
        Shows if the "cost of carry" is peaking or dropping as rates change.
        
        Args:
            years_back: Number of years to look back (default: 5)
            
        Returns:
            List[InterestRatePoint]: Time-series of average interest rates
        """
        endpoint = "/v2/accounting/od/avg_interest_rates"
        
        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=365 * years_back)).date()
        date_filter = f"record_date:gte:{start_date}"
        
        rate_data = []
        
        async with httpx.AsyncClient() as client:
            page = 1
            has_more = True
            
            while has_more:
                params = {
                    "filter": date_filter,
                    "sort": "record_date",
                    "page[size]": 100,
                    "page[number]": page,
                    "format": "json"
                }
                
                response = await client.get(f"{self.BASE_URL}{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("data", [])
                
                if not results:
                    has_more = False
                    break
                
                # Process each record
                for item in results:
                    record_date = item.get("record_date")
                    avg_rate_str = item.get("avg_interest_rate_amt")
                    
                    if record_date and avg_rate_str:
                        try:
                            # Remove commas and convert to float
                            avg_rate = float(avg_rate_str.replace(",", ""))
                            
                            rate_data.append(InterestRatePoint(
                                date=record_date,
                                avg_rate=round(avg_rate, 4)
                            ))
                        except (ValueError, AttributeError):
                            continue
                
                # Check pagination
                meta = data.get("meta", {})
                total_pages = meta.get("total-pages", 0)
                
                if page >= total_pages:
                    has_more = False
                else:
                    page += 1
        
        # Sort by date
        rate_data.sort(key=lambda x: x.date)
        
        return rate_data

    @cache(expire=86400)  # Cache for 24 hours
    async def get_debt_history(self, days_back: int = 365) -> List[DebtPoint]:
        """
        Track total public debt outstanding with daily changes.
        Visualizes the acceleration of debt issuance.
        
        Args:
            days_back: Number of days to look back (default: 365)
            
        Returns:
            List[DebtPoint]: Time-series of debt with daily changes
        """
        endpoint = "/v2/accounting/od/debt_to_penny"
        
        # Calculate date filter
        start_date = (datetime.now() - timedelta(days=days_back)).date()
        date_filter = f"record_date:gte:{start_date}"
        
        debt_records = []
        
        async with httpx.AsyncClient() as client:
            page = 1
            has_more = True
            
            while has_more:
                params = {
                    "filter": date_filter,
                    "sort": "record_date",
                    "page[size]": 100,
                    "page[number]": page,
                    "format": "json"
                }
                
                response = await client.get(f"{self.BASE_URL}{endpoint}", params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get("data", [])
                
                if not results:
                    has_more = False
                    break
                
                # Process each record
                for item in results:
                    record_date = item.get("record_date")
                    debt_str = item.get("tot_pub_debt_out_amt")
                    
                    if record_date and debt_str:
                        try:
                            # Remove commas and convert to float
                            total_debt = float(debt_str.replace(",", ""))
                            
                            debt_records.append({
                                "date": record_date,
                                "total_debt": total_debt
                            })
                        except (ValueError, AttributeError):
                            continue
                
                # Check pagination
                meta = data.get("meta", {})
                total_pages = meta.get("total-pages", 0)
                
                if page >= total_pages:
                    has_more = False
                else:
                    page += 1
        
        # Sort by date
        debt_records.sort(key=lambda x: x["date"])
        
        # Calculate daily changes
        debt_points = []
        for i, record in enumerate(debt_records):
            if i == 0:
                # First record has no previous day
                daily_change = 0.0
            else:
                daily_change = record["total_debt"] - debt_records[i - 1]["total_debt"]
            
            debt_points.append(DebtPoint(
                date=record["date"],
                total_debt=round(record["total_debt"], 2),
                daily_change=round(daily_change, 2)
            ))
        
        return debt_points


