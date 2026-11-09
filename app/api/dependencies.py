from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.sessions import get_session
from app.services.product import ProductService
from app.services.seller import SellerService

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_product_service(session: SessionDep) -> ProductService:
    return ProductService(session)


ProductDep = Annotated[ProductService, Depends(get_product_service)]


def get_seller_service(session: SessionDep) -> SellerService:
    return SellerService(session)


SellerDep = Annotated[SellerService, Depends(get_seller_service)]
