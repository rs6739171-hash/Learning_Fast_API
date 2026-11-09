import random

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


def random_warehouse() -> int:
    return random.randint(1, 5)


class Product(BaseModel):
    name: str = Field(
        description="Product title",
        min_length=3,            # at least 3 characters
        max_length=100,          # at most 100 characters
    )
    price: float = Field(
        description="Price in US dollars",
        gt=0,                    # [g]reater [t]han 0
        le=10_000,               # [l]ess than or [e]qual to 10 000
    )
    stock: int = Field(
        description="Units available in the warehouse",
        ge=0,                    # [g]reater than or [e]qual to 0
    )
    warehouse: int | None = Field(
        description="Warehouse code (1-5). Random if not provided.",
        # default=1,             # fixed default - evaluated ONCE
        default_factory=random_warehouse,   # function REFERENCE - runs per object
    )

class Supplier(BaseModel):
    name: str
    email: str
    country: str = "PK"


class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


if __name__ == "__main__":
    example = ProductCreate(
        name="Wireless Mouse",
        price=18.99,
        stock=42,
    )
    print(example.model_dump())


class ProductStatus(str, Enum):
    active = "active"
    low_stock = "low_stock"
    out_of_stock = "out_of_stock"
    discontinued = "discontinued"

class BaseProduct(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(description="Product title", min_length=3, max_length=100)
    price: float = Field(description="Price in US dollars", gt=0, le=10_000)
    stock: int = Field(description="Units available", ge=0)
    warehouse: int = Field(
        description="Warehouse code (1-5). Random if not provided.",
        default_factory=random_warehouse,
        ge=1,
        le=5,
    )


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    price: float | None = Field(default=None, gt=0, le=10_000)
    stock: int | None = Field(default=None, ge=0)
    warehouse: int | None = Field(default=None, ge=1, le=5)
    status: ProductStatus | None = Field(default=None)


class ProductRead(BaseProduct):
    id: int | None = None
    status: ProductStatus | None = None
