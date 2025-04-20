import asyncio
from crawler.core import extract
from crawler.schema import LambdaGPUCompute, CoreWeaveGPUCompute


async def main():
    tasks = [
        extract(LambdaGPUCompute.url, LambdaGPUCompute.extraction_prompt),
        extract(CoreWeaveGPUCompute.url, CoreWeaveGPUCompute.extraction_prompt),
    ]
    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    asyncio.run(main())
