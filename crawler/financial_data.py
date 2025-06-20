"""
Financial data crawler for Treasury yields, energy futures, and interest rates
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
import aiohttp
from fredapi import Fred
import os
from dotenv import load_dotenv

from crawler.schema import TreasuryYieldModel, EnergyFuturesModel, InterestRateModel

load_dotenv()


class FinancialDataCrawler:
    def __init__(self):
        self.fred_api_key = os.getenv("FRED_API_KEY")
        if self.fred_api_key:
            self.fred = Fred(api_key=self.fred_api_key)
        else:
            self.fred = None
            print("Warning: FRED API key not found. Some data may be unavailable.")

    async def get_treasury_yields(self) -> List[TreasuryYieldModel]:
        """Fetch current Treasury yields"""
        try:
            # Yahoo Finance symbols for Treasury yields
            symbols = {
                "^TNX": "10y",  # 10-Year Treasury
                "^IRX": "3m",   # 3-Month Treasury  
                "^TYX": "30y"   # 30-Year Treasury
            }
            
            results = []
            for symbol, period in symbols.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        current_yield = hist['Close'].iloc[-1]
                        
                        yield_data = {
                            "source": f"yahoo_finance_{symbol}",
                            "yield_10y": current_yield if period == "10y" else None,
                            "yield_2y": None,  # Add 2Y if needed
                            "yield_30y": current_yield if period == "30y" else None
                        }
                        
                        if period == "10y":
                            yield_data["yield_10y"] = current_yield
                        elif period == "30y":
                            yield_data["yield_30y"] = current_yield
                            
                        results.append(TreasuryYieldModel(**yield_data))
                        
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
                    
            return results
            
        except Exception as e:
            print(f"Error in get_treasury_yields: {e}")
            return []

    async def get_energy_futures(self) -> List[EnergyFuturesModel]:
        """Fetch energy futures prices"""
        try:
            symbols = {
                "NG=F": "natural_gas",  # Natural Gas Futures
                "CL=F": "crude_oil",    # Crude Oil Futures
                "HO=F": "heating_oil"   # Heating Oil (proxy for electricity)
            }
            
            results = []
            for symbol, commodity in symbols.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        
                        energy_data = {
                            "source": f"yahoo_finance_{symbol}",
                            "natural_gas_price": current_price if commodity == "natural_gas" else 0.0,
                            "crude_oil_price": current_price if commodity == "crude_oil" else None,
                            "electricity_price": current_price if commodity == "heating_oil" else None
                        }
                        
                        results.append(EnergyFuturesModel(**energy_data))
                        
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
                    
            return results
            
        except Exception as e:
            print(f"Error in get_energy_futures: {e}")
            return []

    async def get_interest_rates(self) -> List[InterestRateModel]:
        """Fetch current interest rates from FRED"""
        try:
            if not self.fred:
                print("FRED API not available")
                return []
                
            # Federal Funds Rate
            fed_funds = self.fred.get_series('FEDFUNDS', limit=1)
            if not fed_funds.empty:
                current_rate = fed_funds.iloc[-1]
                
                rate_data = {
                    "source": "fred_api",
                    "fed_funds_rate": current_rate,
                    "rate_change": None,  # Calculate if needed
                    "next_meeting_date": None  # Add FOMC calendar if needed
                }
                
                return [InterestRateModel(**rate_data)]
            
            return []
            
        except Exception as e:
            print(f"Error in get_interest_rates: {e}")
            return []

    async def get_all_financial_data(self) -> Dict[str, List[Any]]:
        """Fetch all financial data concurrently"""
        tasks = [
            self.get_treasury_yields(),
            self.get_energy_futures(),
            self.get_interest_rates()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "treasury_yields": results[0] if not isinstance(results[0], Exception) else [],
            "energy_futures": results[1] if not isinstance(results[1], Exception) else [],
            "interest_rates": results[2] if not isinstance(results[2], Exception) else []
        }


async def main():
    """Test the financial data crawler"""
    crawler = FinancialDataCrawler()
    data = await crawler.get_all_financial_data()
    
    print("Treasury Yields:")
    for item in data["treasury_yields"]:
        print(f"  {item}")
    
    print("\nEnergy Futures:")
    for item in data["energy_futures"]:
        print(f"  {item}")
    
    print("\nInterest Rates:")
    for item in data["interest_rates"]:
        print(f"  {item}")


if __name__ == "__main__":
    asyncio.run(main())