from redis import RedisError
from app.database.redis import add_jti_to_blacklist
from app.api.dependencies import SessionDep
from app.api.dependencies import get_access_token
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

@router.get("/logout")
async def logout_seller(token_data:Annotated[dict,Depends(get_access_token)]):
    jti=token_data["jti"]
    try:
        await add_jti_to_blacklist(jti)
    except RedisError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,detail="Blacklist service is not available")

    return {"details":"Successfully Logged Out"}