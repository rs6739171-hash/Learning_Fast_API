from redis import RedisError
from app.database.redis import add_jti_to_blacklist
from app.api.dependencies import get_current_seller, SessionDep, get_access_token
from app.database.models import Seller
from app import services
from fastapi import status
from fastapi import HTTPException
from app.utils import decode_access_token
from typing import Annotated
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends
from app.api.schema.product import SellerCreate, SellerRead
from app.api.dependencies import SellerDep
from app.core.security import oauth2_scheme

router = APIRouter(prefix="/seller", tags=["Seller"])


@router.post("/signup", response_model=SellerRead)
async def register_seller(seller: SellerCreate, service: SellerDep) -> SellerRead:
    return await service.add(seller)

@router.post("/login")
async def login(service: SellerDep, request_form: OAuth2PasswordRequestForm = Depends()):
    token = await service.login(request_form.username, request_form.password)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/dashboard", response_model=SellerRead)
@router.get("/me", response_model=SellerRead)
async def get_current_profile(seller: Annotated[Seller, Depends(get_current_seller)]) -> SellerRead:
    if seller is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller not found")
    return seller

@router.get("/logout")
async def logout_seller(token_data:Annotated[dict,Depends(get_access_token)]):
    jti = token_data.get("jti") or token_data.get("jwt")
    if jti:
        await add_jti_to_blacklist(jti)
        return {"details":"Successfully Logged Out"}
    return {"details":"Already Logged Out"}