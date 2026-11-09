from pydantic import EmailStr
from app.api.schema.schemas_fields import ProductStatus
from enum import Enum
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    status: ProductStatus = Field(default=ProductStatus.active)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    warranty_until: datetime | None = Field(default=None)


class Seller(SQLModel, table=True):
    __tablename__ = "sellers"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: EmailStr
    password_hash: str
