#!/usr/bin/env python3
import psycopg2
import logging
from db_config import get_connection_string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def query_all_prices():
    """Query and display all GPU prices from the database"""
    conn_string = get_connection_string()
    
    try:
        # Connect to the database
        conn = psycopg2.connect(conn_string)
        
        # Create a cursor
        with conn.cursor() as cur:
            # Execute the query
            cur.execute("""
                SELECT gpu_model, vram_gb, price_usd, created_at
                FROM gpu_prices
                ORDER BY gpu_model, vram_gb
            """)
            
            # Fetch all results
            rows = cur.fetchall()
            
            # Print the results
            print("\n===== GPU Prices =====")
            print(f"{'GPU Model':<25} {'VRAM (GB)':<10} {'Price (USD)':<12} {'Created At'}")
            print("-" * 70)
            
            for row in rows:
                model, vram, price, created_at = row
                price_str = f"${price:.2f}" if price is not None else "N/A"
                print(f"{model:<25} {vram:<10} {price_str:<12} {created_at}")
                
            print(f"\nTotal records: {len(rows)}")
            
        # Close the connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error querying database: {e}")

if __name__ == "__main__":
    query_all_prices()