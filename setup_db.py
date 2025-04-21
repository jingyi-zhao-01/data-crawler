#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2 import sql
import logging
from mock.serverless_gpu import prices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_url():
    """
    Get the PostgreSQL connection URL from environment variable or use default for development
    """
    return os.environ.get(
        'POSTGRES_URL', 
        'postgresql://postgres:postgres@localhost:5432/gpu_prices'
    )

def create_tables(conn):
    """Create the necessary tables in the database"""
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS gpu_prices (
            id SERIAL PRIMARY KEY,
            gpu_model VARCHAR(100) NOT NULL,
            vram_gb VARCHAR(10) NOT NULL,
            price_usd NUMERIC(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        logger.info("Tables created successfully")

def insert_mock_data(conn):
    """Insert mock data into the database"""
    with conn.cursor() as cur:
        for item in prices:
            # Handle NaN values in price
            price = item['price($)']
            if price == 'NaN':
                price = None
                
            cur.execute(
                """
                INSERT INTO gpu_prices (gpu_model, vram_gb, price_usd)
                VALUES (%s, %s, %s)
                """,
                (
                    item['gpu_model'],
                    item['vram(GB)'],
                    price
                )
            )
        conn.commit()
        logger.info(f"Inserted {len(prices)} records into gpu_prices table")

def main():
    """Main function to set up the database"""
    db_url = get_db_url()
    logger.info(f"Connecting to database: {db_url}")
    
    try:
        conn = psycopg2.connect(db_url)
        create_tables(conn)
        
        # Check if we should insert mock data
        if len(sys.argv) > 1 and sys.argv[1] == '--with-mock-data':
            insert_mock_data(conn)
            
        conn.close()
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()