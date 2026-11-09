from app.services.product import ProductService
from fastapi import Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlmodel import SQLModel,Session
from .models import Product
from .config import settings

# create the databse engine
engine = create_async_engine(settings.POSTGRES_URL, echo=True)

async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def create_db_tables():
    async with engine.begin() as connections:
        await connections.run_sync(SQLModel.metadata.create_all)

async def get_session():
    async with async_session() as session:
        yield session

get_sessions = get_session
SessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_product_service(session:SessionDep):
    return ProductService(session)

ServiceDep = Annotated[ProductService,Depends(get_product_service)]