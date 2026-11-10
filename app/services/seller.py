from app.utils import generate_access_token
from datetime import timezone
from datetime import timedelta
from datetime import datetime
from fastapi import HTTPException
from sqlmodel import select
from app.database.models import Seller
from app.api.schema.product import SellerCreate
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
import jwt
from app.config import security_settings as st

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SellerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, *args, **kwargs) -> Seller | None:
        val = args[-1] if args else kwargs.get("id")
        if isinstance(val, int):
            return await self.session.get(Seller, val)
        if isinstance(val, str):
            res = await self.session.execute(select(Seller).where(Seller.email == val))
            return res.scalar_one_or_none()
        return None

    async def add(self, credentials: SellerCreate) -> Seller:
        seller = Seller(
            **credentials.model_dump(exclude={"password"}),
            password_hash=pwd_context.hash(credentials.password)
        )
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller
    async def login(self,email,password)-> str:
        result = await self.session.execute(select(Seller).where(Seller.email == email))
        seller = result.scalar()

        if seller is None or not pwd_context.verify(password, seller.password_hash):
            raise HTTPException(status_code = 401,detail = "Email is not correct")

        # generate access token
        token = generate_access_token(
            {
                "user": {
                    "id":seller.id
                }
            }
        )
        return token
        