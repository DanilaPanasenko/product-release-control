from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.product_control import BatchModel, ProductModel
from sсhemas.product_control import BatchCreate, Batch, ProductCreate, ProductResponse


class BatchCrud:
    """Класс для круд операций с заданияями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_batch(self, batch_data: BatchCreate) -> Batch:
        """Создания нового задания"""

        try:
            # Используем асинхронный подход (SQLAlchemy 2.0)
            result = await self.session.execute(
                select(BatchModel).where(
                    (BatchModel.batch_number == batch_data.batch_number) &
                    (BatchModel.batch_date == batch_data.batch_date)
                )
            )

            existing_batch = result.scalar_one_or_none()

            if existing_batch:
                raise HTTPException(
                    status_code=400,
                    detail=f"Партия с номером {batch_data.batch_number} и датйо{batch_data.batch_date} уже существует"
                )

            new_batch = BatchModel(**batch_data.model_dump())
            self.session.add(new_batch)
            await self.session.commit()
            await self.session.refresh(new_batch)
            return new_batch

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


class ProductCrud:
    """Класс для круд операций с продуктом"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(self, product_data: ProductCreate):
        """Операция добавления продукта к партиям"""

        result = {
            "added": 0,
            "skipped_existing": 0,
            "skipped_invalid_batch": 0
        }
        for product_item in product_data.products:
            #Проверка существаования продукта
            existing_product = await self.session.execute(
                select(ProductModel).where(
                    ProductModel.unique_code == product_item.unique_code
                )
            )
            if existing_product.scalar_one_or_none():
                result["skipped_existing"] += 1

            #Ищем партию
            batch = await self.session.execute(
                select(BatchModel).where(
                    (BatchModel.batch_date == product_item.batch_date) &
                    (BatchModel.batch_number == product_item.batch_number)
                )
            )
            batch = batch.scalar_one_or_none()
            if not batch:
                result["skipped_invalid_batch"] += 1
                continue

            #Создаем продукт
            new_product = ProductModel(
                unique_code=product_item.unique_code,
                batch_id=batch.id,
                is_aggregated=False,
                aggregated_at=None
            )
            self.session.add(new_product)
            result["added"] += 1
        await self.session.commit()
        return result
