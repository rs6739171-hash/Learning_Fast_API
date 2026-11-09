from pydantic import BaseModel, ConfigDict, EmailStr


class Baseseller(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    email: EmailStr


class SellerCreate(Baseseller):
    password: str


class SellerRead(Baseseller):
    id: int | None = None
