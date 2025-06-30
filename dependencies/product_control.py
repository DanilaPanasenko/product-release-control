from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from crud.crud_batch import BatchCrud, ProductCrud
from db.db import get_db


async def get_batch_creator(db: AsyncSession = Depends(get_db)) -> BatchCrud:
    """Зависимость для получения крудов партии"""

    return BatchCrud(db)


async def get_product_creator(db: AsyncSession = Depends(get_db)) -> ProductCrud:
    """Зависимость для получения крудов продукта"""

    return ProductCrud(db)
