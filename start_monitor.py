#!/usr/bin/env python3
"""
Startup script for CoreWeave Profitability Monitor
"""
import os
import sys
import argparse
import asyncio
from datetime import datetime

def setup_environment():
    """Setup environment and check dependencies"""
    print("CoreWeave Profitability Monitor")
    print("=" * 50)
    print(f"Starting at: {datetime.now()}")
    print()
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("   Copy .env.example to .env and configure your API keys")
        print()
    
    # Check database
    if not os.path.exists('coreweave_profitability.db'):
        print("📊 Setting up database...")
        from storage.setup import setup_tables
        setup_tables('coreweave_profitability.db')
        print("✅ Database setup complete")
        print()

def main():
    parser = argparse.ArgumentParser(description='CoreWeave Profitability Monitor')
    parser.add_argument('--mode', choices=['single', 'continuous', 'scheduled', 'summary', 'dashboard'], 
                       default='single', help='Monitoring mode')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Interval in minutes for continuous mode')
    parser.add_argument('--days', type=int, default=30, 
                       help='Days of historical data to analyze')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode with sample data')
    
    args = parser.parse_args()
    
    setup_environment()
    
    if args.mode == 'dashboard':
        print("🌐 Starting web dashboard...")
        print("   Dashboard will be available at: http://localhost:12000")
        print("   Press Ctrl+C to stop")
        print()
        
        try:
            from dashboard.app import app
            app.run(host='0.0.0.0', port=12000, debug=False)
        except ImportError as e:
            print(f"❌ Error starting dashboard: {e}")
            print("   Install dashboard dependencies: pip install dash plotly")
            sys.exit(1)
    
    elif args.mode == 'summary':
        print("📈 Data Summary:")
        print("-" * 30)
        
        from storage.data_manager import DataManager
        dm = DataManager()
        summary = dm.get_data_summary()
        
        for table, info in summary.items():
            print(f"{table.replace('_', ' ').title()}: {info['count']} records")
            if info['latest_entry']:
                print(f"  Latest: {info['latest_entry']}")
        
        # Show recent alerts
        alerts = dm.get_unresolved_alerts()
        if not alerts.empty:
            print(f"\n🚨 Unresolved Alerts: {len(alerts)}")
            for _, alert in alerts.head(5).iterrows():
                print(f"  {alert['severity'].upper()}: {alert['message'][:80]}...")
        else:
            print("\n✅ No unresolved alerts")
    
    elif args.test:
        print("🧪 Running test mode...")
        asyncio.run(run_test_mode())
    
    else:
        # Set environment variables for the main script
        os.environ['MONITOR_MODE'] = args.mode
        os.environ['MONITOR_INTERVAL'] = str(args.interval)
        
        print(f"🚀 Starting monitor in {args.mode} mode...")
        if args.mode == 'continuous':
            print(f"   Interval: {args.interval} minutes")
        print("   Press Ctrl+C to stop")
        print()
        
        # Import and run the main monitor
        from run import main as run_main
        asyncio.run(run_main())

async def run_test_mode():
    """Run test mode with sample data collection"""
    print("Testing financial data collection...")
    
    try:
        from crawler.financial_data import FinancialDataCrawler
        from storage.data_manager import DataManager
        
        dm = DataManager()
        crawler = FinancialDataCrawler()
        
        # Test financial data collection
        print("  Fetching treasury yields...")
        treasury_data = await crawler.get_treasury_yields()
        print(f"  ✅ Got {len(treasury_data)} treasury yield records")
        
        print("  Fetching energy futures...")
        energy_data = await crawler.get_energy_futures()
        print(f"  ✅ Got {len(energy_data)} energy futures records")
        
        print("  Fetching interest rates...")
        rate_data = await crawler.get_interest_rates()
        print(f"  ✅ Got {len(rate_data)} interest rate records")
        
        # Store test data
        if treasury_data:
            count = dm.store_treasury_yields(treasury_data)
            print(f"  📊 Stored {count} treasury yield records")
        
        if energy_data:
            count = dm.store_energy_futures(energy_data)
            print(f"  📊 Stored {count} energy futures records")
        
        if rate_data:
            count = dm.store_interest_rates(rate_data)
            print(f"  📊 Stored {count} interest rate records")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("   Check your API keys and internet connection")

if __name__ == '__main__':
    main()