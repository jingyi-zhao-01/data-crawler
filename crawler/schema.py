from typing import ClassVar, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# GPU Pricing Extraction
EXTRACTION_PROMPT = """From the crawled content, extract all GPU model and it's price under the section On-demand GPU instances. 
            Do not miss any models in the entire content. if price is not available, return NaN
            One extracted model JSON format should look like this: 
            {"gpu_model": "NVIDIA HGX H100", 'vram(GB)': "10", "price($)": "4.76"}."""

# SEC Filing Extraction
SEC_FILING_PROMPT = """Extract key financial information from SEC filings including:
            - Debt levels and changes
            - Power purchase agreements
            - Capital expenditures
            - Revenue segments
            - Risk factors related to energy costs"""

# News Extraction
NEWS_PROMPT = """Extract key information from news articles including:
            - Hardware launch announcements
            - Supply constraint mentions
            - Energy market developments
            - Company partnerships or contracts"""


class BaseDataModel(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = Field(..., description="Data source identifier")


class GPUPriceModel(BaseDataModel):
    gpu_model: str = Field(..., description="name of the GPU model in cloud service")
    vram: str = Field(..., description="VRAM(GB), e.g. 80")
    price: float = Field(..., description="gpu price per hour")
    extraction_prompt: ClassVar[str] = EXTRACTION_PROMPT


class TreasuryYieldModel(BaseDataModel):
    yield_10y: float = Field(..., description="10-year Treasury yield percentage")
    yield_2y: Optional[float] = Field(None, description="2-year Treasury yield percentage")
    yield_30y: Optional[float] = Field(None, description="30-year Treasury yield percentage")


class EnergyFuturesModel(BaseDataModel):
    natural_gas_price: float = Field(..., description="Natural gas futures price per MMBtu")
    electricity_price: Optional[float] = Field(None, description="Electricity futures price per MWh")
    crude_oil_price: Optional[float] = Field(None, description="Crude oil price per barrel")


class SECFilingModel(BaseDataModel):
    filing_type: str = Field(..., description="Type of SEC filing (10-K, 10-Q, 8-K, etc.)")
    company: str = Field(..., description="Company name")
    filing_date: datetime = Field(..., description="Filing date")
    total_debt: Optional[float] = Field(None, description="Total debt in millions")
    power_contracts: Optional[str] = Field(None, description="Power purchase agreement details")
    capex: Optional[float] = Field(None, description="Capital expenditures in millions")
    key_risks: Optional[List[str]] = Field(None, description="Key risk factors")
    extraction_prompt: ClassVar[str] = SEC_FILING_PROMPT


class EarningsCallModel(BaseDataModel):
    company: str = Field(..., description="Company name")
    quarter: str = Field(..., description="Quarter (e.g., Q1 2024)")
    utilization_rate: Optional[float] = Field(None, description="GPU utilization rate percentage")
    customer_commentary: Optional[str] = Field(None, description="Key customer insights")
    guidance: Optional[str] = Field(None, description="Forward guidance")
    revenue: Optional[float] = Field(None, description="Revenue in millions")


class HardwareNewsModel(BaseDataModel):
    title: str = Field(..., description="News article title")
    content: str = Field(..., description="Article content")
    hardware_type: str = Field(..., description="Hardware type (NVIDIA, AMD, etc.)")
    launch_date: Optional[datetime] = Field(None, description="Product launch date")
    supply_status: Optional[str] = Field(None, description="Supply constraint information")
    extraction_prompt: ClassVar[str] = NEWS_PROMPT


class InterestRateModel(BaseDataModel):
    fed_funds_rate: float = Field(..., description="Federal funds rate percentage")
    rate_change: Optional[float] = Field(None, description="Rate change from previous period")
    next_meeting_date: Optional[datetime] = Field(None, description="Next FOMC meeting date")


class EnergyMarketEventModel(BaseDataModel):
    event_type: str = Field(..., description="Type of event (storm, geopolitical, etc.)")
    description: str = Field(..., description="Event description")
    impact_level: str = Field(..., description="Impact level (low, medium, high)")
    affected_regions: Optional[List[str]] = Field(None, description="Affected geographical regions")


class CloudPlatformPricingModel(BaseDataModel):
    platform: str = Field(..., description="Cloud platform name")
    instance_type: str = Field(..., description="Instance type")
    gpu_type: str = Field(..., description="GPU type")
    price_per_hour: float = Field(..., description="Price per hour")
    availability: str = Field(..., description="Availability status")


# Data source configurations
class LambdaGPUCompute(GPUPriceModel):
    url: ClassVar[str] = "https://lambda.ai/service/gpu-cloud"


class CoreWeaveGPUCompute(GPUPriceModel):
    url: ClassVar[str] = "https://www.coreweave.com/pricing/classic"


class TreasuryData:
    symbols: ClassVar[List[str]] = ["^TNX", "^IRX", "^TYX"]  # 10Y, 3M, 30Y Treasury yields


class EnergyData:
    symbols: ClassVar[List[str]] = ["NG=F", "CL=F"]  # Natural Gas, Crude Oil futures


class SECFilingData:
    companies: ClassVar[List[str]] = ["CoreWeave"]  # Add CIK numbers when available
    filing_types: ClassVar[List[str]] = ["10-K", "10-Q", "8-K", "S-1"]


class NewsSourceData:
    rss_feeds: ClassVar[List[str]] = [
        "https://feeds.feedburner.com/oreilly/radar",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://techcrunch.com/feed/",
    ]
    keywords: ClassVar[List[str]] = [
        "NVIDIA", "AMD", "GPU", "CoreWeave", "cloud computing",
        "data center", "AI infrastructure", "semiconductor"
    ]
