from typing import Optional, List
from pydantic import BaseModel
import sqlite3
from prism import Prism


# Define the Pydantic model
class GPUModel(BaseModel):
    gpu_model: str
    vram: str
    price: Optional[float]


# Define a Prism schema for validation
gpu_prism = Prism(
    {
        "gpu_model": {"type": "string", "required": True},
        "vram": {"type": "string", "required": True},
        "price": {"type": "number", "required": False},
    }
)


class GPUDataService:
    def __init__(self, db_name: str):
        self.db_name = db_name

    def create(self, gpu: GPUModel) -> int:
        """Create a new GPU record and return its ID."""
        # Validate data with Prism
        validated_data = gpu_prism.validate(gpu.dict())
        if not validated_data["valid"]:
            raise ValueError(f"Validation failed: {validated_data['errors']}")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO gpu_models (gpu_model, vram, price)
            VALUES (?, ?, ?)
            """,
            (gpu.gpu_model, gpu.vram, gpu.price),
        )
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        return record_id

    def update(self, record_id: int, gpu: GPUModel) -> bool:
        """Update an existing GPU record by ID."""
        # Validate data with Prism
        validated_data = gpu_prism.validate(gpu.dict())
        if not validated_data["valid"]:
            raise ValueError(f"Validation failed: {validated_data['errors']}")

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE gpu_models
            SET gpu_model = ?, vram = ?, price = ?
            WHERE id = ?
            """,
            (gpu.gpu_model, gpu.vram, gpu.price, record_id),
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success


# TODO: migrate to prism
if __name__ == "__main__":
    DB_NAME = "test.db"

    # Initialize the service
    service = GPUDataService(DB_NAME)

    # Example usage
    new_gpu = GPUModel(gpu_model="NVIDIA RTX 3090", vram="24GB", price=1499.99)
    new_id = service.create(new_gpu)
    print(f"Created record ID: {new_id}")

    updated_gpu = GPUModel(gpu_model="NVIDIA RTX 3090 Ti", vram="24GB", price=1999.99)
    updated = service.update(new_id, updated_gpu)
    print(f"Update successful: {updated}")
