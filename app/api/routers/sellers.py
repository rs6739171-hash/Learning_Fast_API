from fastapi import APIRouter
from app.api.schema.product import SellerCreate, SellerRead
from app.api.dependencies import SellerDep

router = APIRouter(prefix="/seller", tags=["Seller"])


@router.post("/signup", response_model=SellerRead)
async def register_seller(seller: SellerCreate, service: SellerDep) -> SellerRead:
    return await service.add(seller)
