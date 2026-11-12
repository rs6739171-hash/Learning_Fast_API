from datetime import timedelta
from datetime import timezone
from datetime import datetime
from sqlmodel import select
from app.api.schema.schemas_fields import ProductStatus
from app.api.schema.schemas_fields import ProductCreate
from app.models import Product
from sqlalchemy.ext.asyncio import AsyncSession


class ProductService:
    def __init__(self, session: AsyncSession):
        # the service receives the session and keeps it
        self.session = session

    # Get a product by id (None if it does not exist)
    async def get(self, id: int) -> Product | None:
        return await self.session.get(Product, id)

    # Add a new product
    async def add(self, product_create: ProductCreate) -> Product:
        new_product = Product(
            **product_create.model_dump(),
            status=ProductStatus.active,
            warranty_until=datetime.now(timezone.utc) + timedelta(days=365),
        )
        self.session.add(new_product)              # add() is NOT async
        await self.session.commit()
        await self.session.refresh(new_product)
        return new_product

    # Update an existing product (dict = only the fields to change)
    async def update(self, id: int, product_update: dict) -> Product | None:
        product = await self.get(id)
        if product is None:
            return None

        product.sqlmodel_update(product_update)    # NOT async
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    # Delete a product; True if something was deleted
    async def delete(self, id: int) -> bool:
        product = await self.get(id)
        if product is None:
            return False

        await self.session.delete(product)
        await self.session.commit()
        return True