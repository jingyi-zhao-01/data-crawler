"""
SEC filings crawler for CoreWeave and related companies
"""
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

from crawler.schema import SECFilingModel

load_dotenv()


class SECFilingsCrawler:
    def __init__(self):
        self.base_url = "https://www.sec.gov/Archives/edgar/data"
        self.search_url = "https://efts.sec.gov/LATEST/search-index"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; DataCrawler/1.0; +http://example.com/contact)',
            'Accept': 'application/json',
            'Host': 'efts.sec.gov'
        }
        
        # CoreWeave CIK (Central Index Key) - need to find this
        self.company_ciks = {
            "CoreWeave": None,  # Need to find CIK
            # Add other relevant companies
        }

    async def search_company_filings(self, company_name: str, filing_types: List[str] = None, 
                                   days_back: int = 30) -> List[Dict[str, Any]]:
        """Search for company filings"""
        if filing_types is None:
            filing_types = ["10-K", "10-Q", "8-K", "S-1"]
            
        try:
            async with aiohttp.ClientSession() as session:
                # Search for company filings
                search_params = {
                    "q": company_name,
                    "dateRange": "custom",
                    "startdt": (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d"),
                    "enddt": datetime.now().strftime("%Y-%m-%d"),
                    "forms": ",".join(filing_types)
                }
                
                async with session.get(self.search_url, params=search_params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("hits", {}).get("hits", [])
                    else:
                        print(f"Error searching SEC filings: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error in search_company_filings: {e}")
            return []

    async def extract_filing_content(self, filing_url: str) -> Optional[str]:
        """Extract content from SEC filing"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(filing_url, headers=self.headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Parse HTML and extract text
                        soup = BeautifulSoup(content, 'html.parser')
                        return soup.get_text()
                    else:
                        print(f"Error fetching filing content: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error in extract_filing_content: {e}")
            return None

    def parse_financial_data(self, content: str, filing_type: str) -> Dict[str, Any]:
        """Parse financial data from filing content"""
        parsed_data = {
            "total_debt": None,
            "power_contracts": None,
            "capex": None,
            "key_risks": []
        }
        
        try:
            # Extract debt information
            debt_patterns = [
                r"total debt[:\s]+\$?([0-9,]+\.?[0-9]*)\s*(million|billion)?",
                r"long-term debt[:\s]+\$?([0-9,]+\.?[0-9]*)\s*(million|billion)?",
                r"borrowings[:\s]+\$?([0-9,]+\.?[0-9]*)\s*(million|billion)?"
            ]
            
            for pattern in debt_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    amount = float(match.group(1).replace(',', ''))
                    unit = match.group(2)
                    if unit and 'billion' in unit.lower():
                        amount *= 1000  # Convert to millions
                    parsed_data["total_debt"] = amount
                    break
            
            # Extract power contract information
            power_patterns = [
                r"power purchase agreement[s]?[:\s]+(.*?)(?:\.|;|\n)",
                r"electricity contract[s]?[:\s]+(.*?)(?:\.|;|\n)",
                r"energy agreement[s]?[:\s]+(.*?)(?:\.|;|\n)"
            ]
            
            for pattern in power_patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    parsed_data["power_contracts"] = match.group(1).strip()
                    break
            
            # Extract capital expenditures
            capex_patterns = [
                r"capital expenditures?[:\s]+\$?([0-9,]+\.?[0-9]*)\s*(million|billion)?",
                r"capex[:\s]+\$?([0-9,]+\.?[0-9]*)\s*(million|billion)?",
                r"property and equipment additions[:\s]+\$?([0-9,]+\.?[0-9]*)\s*(million|billion)?"
            ]
            
            for pattern in capex_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    amount = float(match.group(1).replace(',', ''))
                    unit = match.group(2)
                    if unit and 'billion' in unit.lower():
                        amount *= 1000
                    parsed_data["capex"] = amount
                    break
            
            # Extract risk factors
            risk_section = re.search(r"risk factors(.*?)(?:item|$)", content, re.IGNORECASE | re.DOTALL)
            if risk_section:
                risk_text = risk_section.group(1)
                # Look for energy-related risks
                energy_risks = re.findall(r"([^.]*(?:energy|power|electricity|gas)[^.]*\.)", risk_text, re.IGNORECASE)
                parsed_data["key_risks"] = [risk.strip() for risk in energy_risks[:5]]  # Limit to 5 risks
            
        except Exception as e:
            print(f"Error parsing financial data: {e}")
        
        return parsed_data

    async def get_coreweave_filings(self, days_back: int = 30) -> List[SECFilingModel]:
        """Get CoreWeave SEC filings"""
        try:
            # Search for CoreWeave filings
            filings = await self.search_company_filings("CoreWeave", days_back=days_back)
            
            results = []
            for filing in filings[:10]:  # Limit to 10 most recent
                try:
                    source = filing.get("_source", {})
                    filing_type = source.get("form", "")
                    company = source.get("display_names", [""])[0]
                    filing_date_str = source.get("file_date", "")
                    
                    # Parse filing date
                    filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d") if filing_date_str else datetime.now()
                    
                    # Get filing URL and extract content
                    filing_url = f"https://www.sec.gov/Archives/edgar/data/{source.get('cik', '')}/{source.get('accession_number', '').replace('-', '')}/{source.get('file_name', '')}"
                    content = await self.extract_filing_content(filing_url)
                    
                    if content:
                        # Parse financial data
                        financial_data = self.parse_financial_data(content, filing_type)
                        
                        filing_model = SECFilingModel(
                            source=f"sec_edgar_{filing_type}",
                            filing_type=filing_type,
                            company=company,
                            filing_date=filing_date,
                            **financial_data
                        )
                        
                        results.append(filing_model)
                        
                except Exception as e:
                    print(f"Error processing filing: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error in get_coreweave_filings: {e}")
            return []

    async def monitor_new_filings(self) -> List[SECFilingModel]:
        """Monitor for new filings in the last 24 hours"""
        return await self.get_coreweave_filings(days_back=1)


async def main():
    """Test the SEC filings crawler"""
    crawler = SECFilingsCrawler()
    filings = await crawler.get_coreweave_filings(days_back=90)
    
    print(f"Found {len(filings)} SEC filings:")
    for filing in filings:
        print(f"  {filing.filing_type} - {filing.company} - {filing.filing_date}")
        if filing.total_debt:
            print(f"    Total Debt: ${filing.total_debt}M")
        if filing.power_contracts:
            print(f"    Power Contracts: {filing.power_contracts[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())