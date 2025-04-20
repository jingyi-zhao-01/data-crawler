from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Any
import asyncio
import sqlite3
from crawler.schema import GPUPriceModel, LambdaGPUCompute, CoreWeaveGPUCompute
from crawler.core import extract


class Transformer(ABC):
    @abstractmethod
    def transform(self, data: Any) -> Any:
        pass


class Storage(ABC):
    @abstractmethod
    def store(self, data: Any) -> None:
        pass


@dataclass
class PriceCleanerTransform(Transformer):
    def transform(self, data: List[GPUPriceModel]) -> List[GPUPriceModel]:
        return [
            GPUPriceModel(
                gpu_model=item.gpu_model.strip(),
                vram=item.vram.replace("GB", "").strip(),
                price=float(str(item.price).replace("$", "").strip())
            )
            for item in data
        ]


@dataclass
class NameNormalizerTransform(Transformer):
    def transform(self, data: List[GPUPriceModel]) -> List[GPUPriceModel]:
        return [
            GPUPriceModel(
                gpu_model=item.gpu_model.upper(),
                vram=item.vram,
                price=item.price
            )
            for item in data
        ]


class SQLiteStorage(Storage):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def store(self, data: List[GPUPriceModel]) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gpu_prices
            (gpu_model TEXT, vram TEXT, price REAL)
        ''')

        for item in data:
            cursor.execute(
                'INSERT INTO gpu_prices VALUES (?, ?, ?)',
                (item.gpu_model, item.vram, item.price)
            )

        conn.commit()
        conn.close()


class GPUPricePipeline:
    def __init__(self, transformers: List[Transformer], storage: Storage):
        self.transformers = transformers
        self.storage = storage

    async def process(self, data: Any) -> Any:
        result = data
        for transformer in self.transformers:
            print(f"Applying {transformer.__class__.__name__}...")
            result = transformer.transform(result)

        print("Storing data...")
        self.storage.store(result)
        return result


async def main():
    # Define pipeline
    pipeline = GPUPricePipeline(
        transformers=[
            PriceCleanerTransform(),
            NameNormalizerTransform(),
        ],
        storage=SQLiteStorage("gpu_prices.db")
    )

    # Extract data
    tasks = [
        extract(LambdaGPUCompute.url, LambdaGPUCompute.extraction_prompt),
        extract(CoreWeaveGPUCompute.url, CoreWeaveGPUCompute.extraction_prompt),
    ]
    raw_data = await asyncio.gather(*tasks)

    # Flatten results
    flattened_data = [item for sublist in raw_data for item in sublist]

    # Process through pipeline
    processed_data = await pipeline.process(flattened_data)
    return processed_data


if __name__ == "__main__":
    asyncio.run(main())
