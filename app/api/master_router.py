from .routers import product, sellers
from fastapi import APIRouter

router = APIRouter()

router.include_router(sellers.router)
router.include_router(product.router)

