from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from crud.crud_batch import BatchCrud, ProductCrud
from db.db import engine, Base, AsyncSessionLocal, get_db
from dependencies.product_control import get_batch_creator, get_product_creator
from models.product_control import BatchModel
from sсhemas.product_control import BatchCreate, Batch, ProductCreate, ProductResponse

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
    batch_data: BatchCreate,
    crud: BatchCrud = Depends(get_batch_creator)
) -> Batch:
    """Эндпоинт создания сменного задания"""

    return await crud.create_batch(batch_data)


@app.post("/add_product/", response_model=ProductResponse)
async def create_product(
        product_data: ProductCreate,
        crud: ProductCrud = Depends(get_product_creator)
) -> ProductResponse:
    """Эндпоинт создания продукта"""

    return await crud.create_product(product_data)
