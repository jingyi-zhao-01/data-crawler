"""
Data manager for storing and retrieving all types of profitability indicators
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from contextlib import contextmanager

from crawler.schema import (
    GPUPriceModel, TreasuryYieldModel, EnergyFuturesModel, SECFilingModel,
    EarningsCallModel, HardwareNewsModel, InterestRateModel, 
    EnergyMarketEventModel, CloudPlatformPricingModel
)


class DataManager:
    def __init__(self, db_path: str = "coreweave_profitability.db"):
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database and tables exist"""
        from storage.setup import setup_tables
        setup_tables(self.db_path)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    # GPU Pricing Methods
    def store_gpu_pricing(self, gpu_data: List[GPUPriceModel]) -> int:
        """Store GPU pricing data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for gpu in gpu_data:
                cursor.execute(
                    """
                    INSERT INTO gpu_pricing (timestamp, source, gpu_model, vram, price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (gpu.timestamp, gpu.source, gpu.gpu_model, gpu.vram, gpu.price)
                )
                count += 1
            conn.commit()
            return count

    def get_gpu_pricing(self, days_back: int = 30, source: Optional[str] = None) -> pd.DataFrame:
        """Get GPU pricing data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM gpu_pricing 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days_back)
            
            params = []
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY timestamp DESC"
            
            return pd.read_sql_query(query, conn, params=params)

    # Treasury Yields Methods
    def store_treasury_yields(self, yield_data: List[TreasuryYieldModel]) -> int:
        """Store treasury yield data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for yield_item in yield_data:
                cursor.execute(
                    """
                    INSERT INTO treasury_yields (timestamp, source, yield_10y, yield_2y, yield_30y)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (yield_item.timestamp, yield_item.source, yield_item.yield_10y, 
                     yield_item.yield_2y, yield_item.yield_30y)
                )
                count += 1
            conn.commit()
            return count

    def get_treasury_yields(self, days_back: int = 30) -> pd.DataFrame:
        """Get treasury yield data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM treasury_yields 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            """.format(days_back)
            
            return pd.read_sql_query(query, conn)

    # Energy Futures Methods
    def store_energy_futures(self, energy_data: List[EnergyFuturesModel]) -> int:
        """Store energy futures data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for energy in energy_data:
                cursor.execute(
                    """
                    INSERT INTO energy_futures (timestamp, source, natural_gas_price, electricity_price, crude_oil_price)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (energy.timestamp, energy.source, energy.natural_gas_price, 
                     energy.electricity_price, energy.crude_oil_price)
                )
                count += 1
            conn.commit()
            return count

    def get_energy_futures(self, days_back: int = 30) -> pd.DataFrame:
        """Get energy futures data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM energy_futures 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            """.format(days_back)
            
            return pd.read_sql_query(query, conn)

    # SEC Filings Methods
    def store_sec_filings(self, filing_data: List[SECFilingModel]) -> int:
        """Store SEC filing data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for filing in filing_data:
                key_risks_json = json.dumps(filing.key_risks) if filing.key_risks else None
                cursor.execute(
                    """
                    INSERT INTO sec_filings (timestamp, source, filing_type, company, filing_date, 
                                           total_debt, power_contracts, capex, key_risks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (filing.timestamp, filing.source, filing.filing_type, filing.company,
                     filing.filing_date, filing.total_debt, filing.power_contracts, 
                     filing.capex, key_risks_json)
                )
                count += 1
            conn.commit()
            return count

    def get_sec_filings(self, days_back: int = 90, company: Optional[str] = None) -> pd.DataFrame:
        """Get SEC filing data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM sec_filings 
                WHERE filing_date >= datetime('now', '-{} days')
            """.format(days_back)
            
            params = []
            if company:
                query += " AND company LIKE ?"
                params.append(f"%{company}%")
            
            query += " ORDER BY filing_date DESC"
            
            return pd.read_sql_query(query, conn, params=params)

    # Hardware News Methods
    def store_hardware_news(self, news_data: List[HardwareNewsModel]) -> int:
        """Store hardware news data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for news in news_data:
                cursor.execute(
                    """
                    INSERT INTO hardware_news (timestamp, source, title, content, hardware_type, 
                                             launch_date, supply_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (news.timestamp, news.source, news.title, news.content, 
                     news.hardware_type, news.launch_date, news.supply_status)
                )
                count += 1
            conn.commit()
            return count

    def get_hardware_news(self, days_back: int = 30, hardware_type: Optional[str] = None) -> pd.DataFrame:
        """Get hardware news data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM hardware_news 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days_back)
            
            params = []
            if hardware_type:
                query += " AND hardware_type = ?"
                params.append(hardware_type)
            
            query += " ORDER BY timestamp DESC"
            
            return pd.read_sql_query(query, conn, params=params)

    # Interest Rates Methods
    def store_interest_rates(self, rate_data: List[InterestRateModel]) -> int:
        """Store interest rate data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for rate in rate_data:
                cursor.execute(
                    """
                    INSERT INTO interest_rates (timestamp, source, fed_funds_rate, rate_change, next_meeting_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rate.timestamp, rate.source, rate.fed_funds_rate, 
                     rate.rate_change, rate.next_meeting_date)
                )
                count += 1
            conn.commit()
            return count

    def get_interest_rates(self, days_back: int = 30) -> pd.DataFrame:
        """Get interest rate data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM interest_rates 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            """.format(days_back)
            
            return pd.read_sql_query(query, conn)

    # Energy Market Events Methods
    def store_energy_events(self, event_data: List[EnergyMarketEventModel]) -> int:
        """Store energy market event data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for event in event_data:
                affected_regions_json = json.dumps(event.affected_regions) if event.affected_regions else None
                cursor.execute(
                    """
                    INSERT INTO energy_market_events (timestamp, source, event_type, description, 
                                                    impact_level, affected_regions)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (event.timestamp, event.source, event.event_type, event.description,
                     event.impact_level, affected_regions_json)
                )
                count += 1
            conn.commit()
            return count

    def get_energy_events(self, days_back: int = 30, impact_level: Optional[str] = None) -> pd.DataFrame:
        """Get energy market event data"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM energy_market_events 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days_back)
            
            params = []
            if impact_level:
                query += " AND impact_level = ?"
                params.append(impact_level)
            
            query += " ORDER BY timestamp DESC"
            
            return pd.read_sql_query(query, conn, params=params)

    # Alert Methods
    def create_alert(self, alert_type: str, message: str, severity: str, data_source: str):
        """Create a new alert"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alerts (alert_type, message, severity, data_source)
                VALUES (?, ?, ?, ?)
                """,
                (alert_type, message, severity, data_source)
            )
            conn.commit()

    def get_unresolved_alerts(self) -> pd.DataFrame:
        """Get unresolved alerts"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM alerts 
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            """
            
            return pd.read_sql_query(query, conn)

    def resolve_alert(self, alert_id: int):
        """Mark an alert as resolved"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE alerts SET resolved = TRUE WHERE id = ?",
                (alert_id,)
            )
            conn.commit()

    # Analysis Methods
    def store_correlation_analysis(self, metric_1: str, metric_2: str, correlation: float, 
                                 p_value: Optional[float], period_days: int, notes: Optional[str] = None):
        """Store correlation analysis results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO correlation_analysis (metric_1, metric_2, correlation_coefficient, 
                                                p_value, analysis_period_days, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (metric_1, metric_2, correlation, p_value, period_days, notes)
            )
            conn.commit()

    def get_correlation_analysis(self, days_back: int = 30) -> pd.DataFrame:
        """Get correlation analysis results"""
        with self.get_connection() as conn:
            query = """
                SELECT * FROM correlation_analysis 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            """.format(days_back)
            
            return pd.read_sql_query(query, conn)

    # Summary Methods
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of all data in the database"""
        with self.get_connection() as conn:
            summary = {}
            
            tables = [
                'gpu_pricing', 'treasury_yields', 'energy_futures', 'sec_filings',
                'hardware_news', 'interest_rates', 'energy_market_events', 'alerts'
            ]
            
            for table in tables:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT MAX(timestamp) as latest FROM {table}")
                latest = cursor.fetchone()[0]
                
                summary[table] = {
                    'count': count,
                    'latest_entry': latest
                }
            
            return summary


# Example usage and testing
if __name__ == "__main__":
    dm = DataManager()
    
    # Test data summary
    summary = dm.get_data_summary()
    print("Data Summary:")
    for table, info in summary.items():
        print(f"  {table}: {info['count']} records, latest: {info['latest_entry']}")
    
    # Test alert creation
    dm.create_alert("price_spike", "GPU prices increased by 20%", "high", "lambda_labs")
    
    # Get unresolved alerts
    alerts = dm.get_unresolved_alerts()
    print(f"\nUnresolved alerts: {len(alerts)}")
    for _, alert in alerts.iterrows():
        print(f"  {alert['alert_type']}: {alert['message']}")