from typing import Any
from fastapi import FastAPI, HTTPException,status
from schemas_fields import ProductCreate,ProductRead,ProductUpdate,ProductStatus
from database import Database

db = Database()
app = FastAPI()

@app.get("/product",response_model = ProductRead)
def get_product(id:int)->dict:

    product = db.get(id)
    if product is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Product with the given ID not found!",
        )

    return product

@app.post("/product")
def create_product(data:ProductCreate)->dict[str,Any]:
    new_id = db.create(data)
    return {"id":new_id}


@app.patch("/product", response_model=ProductRead)
def update_product(id: int,body:ProductUpdate)->dict[str,Any]:
    updated = db.update(id,body)
    if updated is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail = "Product with the given id was not found!"
        )
    return updated

@app.delete("/product")
def delete_product(id: int) -> dict[str, str]:
    db.delete(id)

    return {"detail":f"Deleted the product with ID{id}"}