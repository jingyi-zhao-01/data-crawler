"""
CoreWeave Profitability Indicators Data Crawler
Main orchestrator for collecting all profitability-related data
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

from crawler.core import extract
from crawler.schema import LambdaGPUCompute, CoreWeaveGPUCompute
from crawler.financial_data import FinancialDataCrawler
from crawler.sec_filings import SECFilingsCrawler
from crawler.news_crawler import NewsCrawler
from storage.data_manager import DataManager
from alerts.alert_system import AlertSystem, ConsoleNotifier

load_dotenv()


class CoreWeaveProfitabilityMonitor:
    def __init__(self):
        self.data_manager = DataManager()
        self.financial_crawler = FinancialDataCrawler()
        self.sec_crawler = SECFilingsCrawler()
        self.news_crawler = NewsCrawler()
        self.alert_system = AlertSystem(self.data_manager)
        
        # Setup alert notifications
        self.alert_system.add_notification_channel(ConsoleNotifier())
        
        self.last_run_times = {}

    async def collect_gpu_pricing(self) -> Dict[str, Any]:
        """Collect GPU pricing data from Lambda Labs and CoreWeave"""
        print("Collecting GPU pricing data...")
        try:
            tasks = [
                extract(LambdaGPUCompute.url, LambdaGPUCompute.extraction_prompt),
                extract(CoreWeaveGPUCompute.url, CoreWeaveGPUCompute.extraction_prompt),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process and store results
            gpu_data = []
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result:
                    source = "lambda_labs" if i == 0 else "coreweave"
                    # Parse the extracted content and create GPUPriceModel instances
                    # This would need to be implemented based on the actual extraction format
                    print(f"GPU data from {source}: {result}")
            
            return {"gpu_pricing": gpu_data, "status": "success"}
            
        except Exception as e:
            print(f"Error collecting GPU pricing: {e}")
            return {"gpu_pricing": [], "status": "error", "error": str(e)}

    async def collect_financial_data(self) -> Dict[str, Any]:
        """Collect financial market data"""
        print("Collecting financial market data...")
        try:
            financial_data = await self.financial_crawler.get_all_financial_data()
            
            # Store data
            if financial_data["treasury_yields"]:
                count = self.data_manager.store_treasury_yields(financial_data["treasury_yields"])
                print(f"Stored {count} treasury yield records")
            
            if financial_data["energy_futures"]:
                count = self.data_manager.store_energy_futures(financial_data["energy_futures"])
                print(f"Stored {count} energy futures records")
            
            if financial_data["interest_rates"]:
                count = self.data_manager.store_interest_rates(financial_data["interest_rates"])
                print(f"Stored {count} interest rate records")
            
            return {"financial_data": financial_data, "status": "success"}
            
        except Exception as e:
            print(f"Error collecting financial data: {e}")
            return {"financial_data": {}, "status": "error", "error": str(e)}

    async def collect_sec_filings(self) -> Dict[str, Any]:
        """Collect SEC filings data"""
        print("Collecting SEC filings...")
        try:
            filings = await self.sec_crawler.get_coreweave_filings(days_back=7)
            
            if filings:
                count = self.data_manager.store_sec_filings(filings)
                print(f"Stored {count} SEC filing records")
            
            return {"sec_filings": filings, "status": "success"}
            
        except Exception as e:
            print(f"Error collecting SEC filings: {e}")
            return {"sec_filings": [], "status": "error", "error": str(e)}

    async def collect_news_data(self) -> Dict[str, Any]:
        """Collect news and market events"""
        print("Collecting news and market events...")
        try:
            news_data = await self.news_crawler.get_all_news()
            
            # Store data
            if news_data["hardware_news"]:
                count = self.data_manager.store_hardware_news(news_data["hardware_news"])
                print(f"Stored {count} hardware news records")
            
            if news_data["energy_events"]:
                count = self.data_manager.store_energy_events(news_data["energy_events"])
                print(f"Stored {count} energy event records")
            
            return {"news_data": news_data, "status": "success"}
            
        except Exception as e:
            print(f"Error collecting news data: {e}")
            return {"news_data": {}, "status": "error", "error": str(e)}

    async def run_full_collection_cycle(self) -> Dict[str, Any]:
        """Run a complete data collection cycle"""
        print(f"\n{'='*60}")
        print(f"Starting CoreWeave Profitability Data Collection")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        results = {}
        
        # Collect all data types
        collection_tasks = [
            ("gpu_pricing", self.collect_gpu_pricing()),
            ("financial_data", self.collect_financial_data()),
            ("sec_filings", self.collect_sec_filings()),
            ("news_data", self.collect_news_data())
        ]
        
        for task_name, task in collection_tasks:
            try:
                result = await task
                results[task_name] = result
                print(f"✓ {task_name}: {result['status']}")
            except Exception as e:
                results[task_name] = {"status": "error", "error": str(e)}
                print(f"✗ {task_name}: error - {e}")
        
        # Run alert monitoring
        try:
            print("\nRunning alert monitoring...")
            alerts = await self.alert_system.run_monitoring_cycle()
            results["alerts"] = {"count": len(alerts), "alerts": alerts}
        except Exception as e:
            print(f"Error in alert monitoring: {e}")
            results["alerts"] = {"count": 0, "error": str(e)}
        
        # Print summary
        print(f"\n{'='*60}")
        print("Collection Summary:")
        for task_name, result in results.items():
            status = result.get("status", "unknown")
            print(f"  {task_name}: {status}")
        print(f"{'='*60}\n")
        
        return results

    async def run_monitoring_mode(self, interval_minutes: int = 60):
        """Run continuous monitoring mode"""
        print(f"Starting continuous monitoring mode (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                await self.run_full_collection_cycle()
                
                # Wait for next cycle
                print(f"Waiting {interval_minutes} minutes until next collection cycle...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("Monitoring stopped by user")
                break
            except Exception as e:
                print(f"Error in monitoring cycle: {e}")
                print("Waiting 5 minutes before retry...")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

    def setup_scheduled_collection(self):
        """Setup scheduled data collection using the schedule library"""
        # High-frequency data (every 15 minutes)
        schedule.every(15).minutes.do(lambda: asyncio.run(self.collect_gpu_pricing()))
        schedule.every(15).minutes.do(lambda: asyncio.run(self.collect_financial_data()))
        
        # Medium-frequency data (every hour)
        schedule.every().hour.do(lambda: asyncio.run(self.collect_news_data()))
        
        # Low-frequency data (every 4 hours)
        schedule.every(4).hours.do(lambda: asyncio.run(self.collect_sec_filings()))
        
        # Alert monitoring (every 30 minutes)
        schedule.every(30).minutes.do(lambda: asyncio.run(self.alert_system.run_monitoring_cycle()))
        
        print("Scheduled collection setup complete:")
        print("  - GPU pricing & financial data: every 15 minutes")
        print("  - News data: every hour")
        print("  - SEC filings: every 4 hours")
        print("  - Alert monitoring: every 30 minutes")

    def run_scheduled_mode(self):
        """Run in scheduled mode using the schedule library"""
        self.setup_scheduled_collection()
        
        print("Starting scheduled monitoring mode...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("Scheduled monitoring stopped by user")

    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of collected data"""
        summary = self.data_manager.get_data_summary()
        
        print("\nData Summary:")
        print("-" * 40)
        for table, info in summary.items():
            print(f"{table}: {info['count']} records")
            if info['latest_entry']:
                print(f"  Latest: {info['latest_entry']}")
        print("-" * 40)
        
        return summary


async def main():
    """Main entry point"""
    monitor = CoreWeaveProfitabilityMonitor()
    
    # Check command line arguments or environment variables for mode
    mode = os.getenv("MONITOR_MODE", "single")
    
    if mode == "continuous":
        interval = int(os.getenv("MONITOR_INTERVAL", "60"))
        await monitor.run_monitoring_mode(interval_minutes=interval)
    elif mode == "scheduled":
        monitor.run_scheduled_mode()
    elif mode == "summary":
        monitor.get_data_summary()
    else:
        # Single run mode
        await monitor.run_full_collection_cycle()


if __name__ == "__main__":
    asyncio.run(main())
