from app.api.routers import product
from app.api import master_router
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .sessions import create_db_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
   await create_db_tables()
   yield

app = FastAPI(lifespan=lifespan)

app.include_router(master_router.router)


