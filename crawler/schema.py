from typing import ClassVar

from pydantic import BaseModel, Field

EXTRACTION_PROMPT = """From the crawled content, extract all GPU model and it's price under the section On-demand GPU instances. 
            Do not miss any models in the entire content. if price is not available, return NaN
            One extracted model JSON format should look like this: 
            {"gpu_model": "NVIDIA HGX H100", 'vram(GB)': "10", "price($)": "4.76"}."""


class GPUPriceModel(BaseModel):
    gpu_model: str = Field(..., description="name of the GPU model in cloud service")
    vram: str = Field(..., description="VRAM(GB), e.g. 80")
    price: float = Field(..., description="gpu price per hour")
    extraction_prompt: ClassVar[str] = EXTRACTION_PROMPT


class LambdaGPUCompute(GPUPriceModel):
    url: ClassVar[str] = "https://lambda.ai/service/gpu-cloud"


class CoreWeaveGPUCompute(GPUPriceModel):
    url: ClassVar[str] = "https://www.coreweave.com/pricing/classic"
