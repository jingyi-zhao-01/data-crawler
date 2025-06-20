import sqlite3
from datetime import datetime


def setup_tables(db_name: str):
    """Create required tables in the database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create gpu_pricing table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gpu_pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            gpu_model TEXT NOT NULL,
            vram TEXT NOT NULL,
            price REAL NOT NULL
        )
        """
    )

    # Create treasury_yields table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS treasury_yields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            yield_10y REAL,
            yield_2y REAL,
            yield_30y REAL
        )
        """
    )

    # Create energy_futures table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_futures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            natural_gas_price REAL NOT NULL,
            electricity_price REAL,
            crude_oil_price REAL
        )
        """
    )

    # Create sec_filings table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sec_filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            filing_type TEXT NOT NULL,
            company TEXT NOT NULL,
            filing_date DATETIME NOT NULL,
            total_debt REAL,
            power_contracts TEXT,
            capex REAL,
            key_risks TEXT
        )
        """
    )

    # Create earnings_calls table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS earnings_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            company TEXT NOT NULL,
            quarter TEXT NOT NULL,
            utilization_rate REAL,
            customer_commentary TEXT,
            guidance TEXT,
            revenue REAL
        )
        """
    )

    # Create hardware_news table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hardware_news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            hardware_type TEXT,
            launch_date DATETIME,
            supply_status TEXT
        )
        """
    )

    # Create interest_rates table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS interest_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            fed_funds_rate REAL NOT NULL,
            rate_change REAL,
            next_meeting_date DATETIME
        )
        """
    )

    # Create energy_market_events table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_market_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            impact_level TEXT NOT NULL,
            affected_regions TEXT
        )
        """
    )

    # Create cloud_platform_pricing table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cloud_platform_pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            platform TEXT NOT NULL,
            instance_type TEXT NOT NULL,
            gpu_type TEXT NOT NULL,
            price_per_hour REAL NOT NULL,
            availability TEXT
        )
        """
    )

    # Create alerts table for monitoring
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            data_source TEXT NOT NULL,
            resolved BOOLEAN DEFAULT FALSE
        )
        """
    )

    # Create correlation_analysis table for storing analysis results
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS correlation_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            metric_1 TEXT NOT NULL,
            metric_2 TEXT NOT NULL,
            correlation_coefficient REAL NOT NULL,
            p_value REAL,
            analysis_period_days INTEGER NOT NULL,
            notes TEXT
        )
        """
    )

    # Create indexes for better performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_gpu_pricing_timestamp ON gpu_pricing(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_treasury_yields_timestamp ON treasury_yields(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_energy_futures_timestamp ON energy_futures(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_sec_filings_company ON sec_filings(company, filing_date)",
        "CREATE INDEX IF NOT EXISTS idx_hardware_news_hardware_type ON hardware_news(hardware_type, timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved, timestamp)"
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    conn.commit()
    conn.close()


def insert_sample_data(db_name: str):
    """Insert sample data for testing."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Sample GPU pricing data
    cursor.execute(
        """
        INSERT INTO gpu_pricing (source, gpu_model, vram, price)
        VALUES ('lambda_labs', 'NVIDIA H100', '80', 4.76)
        """
    )

    # Sample treasury yield data
    cursor.execute(
        """
        INSERT INTO treasury_yields (source, yield_10y)
        VALUES ('yahoo_finance', 4.25)
        """
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    DB_NAME = "coreweave_profitability.db"
    setup_tables(DB_NAME)
    insert_sample_data(DB_NAME)
    print(f"Tables set up in database: {DB_NAME}")
    print("Sample data inserted for testing")
