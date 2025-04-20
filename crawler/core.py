import os
import asyncio

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
)
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from dotenv import load_dotenv

from crawler.schema import GPUPriceModel, LambdaGPUCompute

load_dotenv()


async def extract(url, prompt):
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
            # Here you can use any provider that Litellm library supports, for instance: ollama/qwen2
            # provider="ollama/qwen2", api_token="no-token",
            llm_config=LLMConfig(
                provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY")
            ),
            schema=GPUPriceModel.schema(),
            extraction_type="schema",
            instruction=prompt,
        ),
        cache_mode=CacheMode.BYPASS,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)

        result = result.extracted_content
        print(result)
        return result


if __name__ == "__main__":
    asyncio.run(extract(LambdaGPUCompute.url, LambdaGPUCompute.extraction_prompt))
    print("-----------------------------------------------------------")
    # asyncio.run(extract("https://lambda.ai/service/gpu-cloud"))
