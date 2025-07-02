from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from crud.crud_batch import BatchCrud, ProductCrud
from db.db import engine, Base, get_db
from dependencies.product_control import get_batch_creator, get_product_creator
from sсhemas.product_control import (
    BatchCreate,
    Batch,
    ProductCreate,
    ProductResponse,
    BatchAndProduct,
    BatchUpdate,
)

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Функция для очистки и создания БД, использовать только во время разработки"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем старую
        await conn.run_sync(Base.metadata.create_all)  # Создаем новую


@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "Database connection OK"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.post("/add_batch/", response_model=Batch)
async def create_batch(
    batch_data: BatchCreate, crud: BatchCrud = Depends(get_batch_creator)
) -> Batch:
    """Эндпоинт создания сменного задания"""

    return await crud.create_batch(batch_data)


@app.post("/add_product/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate, crud: ProductCrud = Depends(get_product_creator)
) -> ProductResponse:
    """Эндпоинт создания продукта"""

    return await crud.create_product(product_data)


@app.get("/get_batch/", response_model=BatchAndProduct)
async def get_batch_id(batch_id: int, crud: BatchCrud = Depends(get_batch_creator)):
    """Эндпоинт для получения сменного задания по id"""

    return await crud.get_batch(batch_id)


@app.patch("/update/{batch_id}", response_model=BatchUpdate)
async def update_batch_id(
    batch_id: int,
    update_data: BatchUpdate,
    crud: BatchCrud = Depends(get_batch_creator),
):
    update_batch = await crud.update_batch(batch_id, update_data)
    if not update_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Партия с ID: {batch_id} не найдена",
        )
    return update_batch
