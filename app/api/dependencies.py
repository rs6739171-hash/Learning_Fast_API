from app.database.redis import is_jti_blacklisted
from app.database.models import Seller
from app.core.security import oauth2_scheme
from fastapi import status
from fastapi import HTTPException
from app.utils import decode_access_token
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

async def get_access_token(token:Annotated[str,Depends(oauth2_scheme)])-> dict:
    data = decode_access_token(token)
    jti = data.get("jti") or data.get("jwt") if data else None
    if data is None or not jti or await is_jti_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )
    return data

def get_seller_service(session: SessionDep) -> SellerService:
    return SellerService(session)


SellerDep = Annotated[SellerService, Depends(get_seller_service)]


# Get logged in seller
async def get_current_seller(token_data: Annotated[dict, Depends(get_access_token)], service: SellerDep) -> Seller:
    user_id = token_data.get("user", {}).get("id") or token_data.get("user", {}).get("email")
    seller = await service.get(user_id)
    return seller
