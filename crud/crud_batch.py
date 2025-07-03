from datetime import datetime
from typing import Optional, Type, List, Dict, Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.product_control import BatchModel, ProductModel
from sсhemas.product_control import (
    BatchCreate,
    Batch,
    ProductCreate,
    BatchAndProduct,
    BatchUpdate, BatchFilter,
)


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
                    (BatchModel.batch_number == batch_data.batch_number)
                    & (BatchModel.batch_date == batch_data.batch_date)
                )
            )

            existing_batch = result.scalar_one_or_none()

            if existing_batch:
                raise HTTPException(
                    status_code=400,
                    detail=f"Партия с номером {batch_data.batch_number} и датйо{batch_data.batch_date} уже существует",
                )

            new_batch = BatchModel(**batch_data.model_dump())
            self.session.add(new_batch)
            await self.session.commit()
            await self.session.refresh(new_batch)
            return new_batch

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def get_batch(self, batch_id: int) -> Optional[BatchAndProduct]:
        """Получаем сменное задание вместе со списком уникальных кодов продукции"""

        result = await self.session.execute(
            select(BatchModel)
            .where(BatchModel.id == batch_id)
            .options(selectinload(BatchModel.products))
        )
        batch = result.scalar_one_or_none()
        return BatchAndProduct.model_validate(batch)

    async def update_batch(
        self, batch_id: int, update_data: BatchUpdate
    ) -> Type[BatchModel] | None:
        """Обновляем задание и при закрытии сменного задания ставим дату закрытия в поле closed_at"""
        # Получаем только установленные поля
        update_values = update_data.model_dump(exclude_unset=True)

        # Обрабатываем is_closed отдельно
        if "is_closed" in update_values:
            is_closed_data = update_values.pop("is_closed")
            if isinstance(is_closed_data, dict):  # Если пришло из валидатора
                update_values.update(is_closed_data)
            else:
                update_values["closed_at"] = datetime.now() if is_closed_data else None

        if not update_values:  # Нет полей для обновления
            return await self.session.get(BatchModel, batch_id)

        # Выполняем обновление
        result = await self.session.execute(
            update(BatchModel)
            .where(BatchModel.id == batch_id)
            .values(**update_values)
            .returning(BatchModel)
        )

        batch = result.scalar_one_or_none()
        if batch:
            await self.session.commit()
        return batch

    async def get_batches_filter(self, batch_filter: BatchFilter) -> List[Dict[str, Any]]:
        """Получение сменных заданий по фильтрам"""

        query = select(BatchModel)
        filters = []

        if batch_filter.is_closed:
            filters.append(BatchModel.is_closed == batch_filter.is_closed)
        if batch_filter.work_center:
            filters.append(BatchModel.work_center == batch_filter.work_center)
        if batch_filter.shift:
            filters.append(BatchModel.shift == batch_filter.shift)
        if batch_filter.team:
            filters.append(BatchModel.team == batch_filter.team)
        if batch_filter.batch_number:
            filters.append(BatchModel.batch_number == batch_filter.batch_number)
        if batch_filter.batch_date:
            filters.append(BatchModel.batch_date == batch_filter.batch_date)
        if batch_filter.work_center_id:
            filters.append(BatchModel.work_center_id == batch_filter.work_center_id)

        if filters:
            query = query.where(and_(*filters))

        if batch_filter.limit:
            query = query.limit(batch_filter.limit)
        if batch_filter.offset:
            query = query.offset(batch_filter.offset)

        result = await self.session.execute(query)
        return jsonable_encoder(result.scalars().all())


class ProductCrud:
    """Класс для круд операций с продуктом"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(self, product_data: ProductCreate):
        """Операция добавления продукта к партиям"""

        result = {"added": 0, "skipped_existing": 0, "skipped_invalid_batch": 0}
        for product_item in product_data.products:
            # Проверка существаования продукта
            existing_product = await self.session.execute(
                select(ProductModel).where(
                    ProductModel.unique_code == product_item.unique_code
                )
            )
            if existing_product.scalar_one_or_none():
                result["skipped_existing"] += 1

            # Ищем партию
            batch = await self.session.execute(
                select(BatchModel).where(
                    (BatchModel.batch_date == product_item.batch_date)
                    & (BatchModel.batch_number == product_item.batch_number)
                )
            )
            batch = batch.scalar_one_or_none()
            if not batch:
                result["skipped_invalid_batch"] += 1
                continue

            # Создаем продукт
            new_product = ProductModel(
                unique_code=product_item.unique_code,
                batch_id=batch.id,
                is_aggregated=False,
                aggregated_at=None,
            )
            self.session.add(new_product)
            result["added"] += 1
        await self.session.commit()
        return result
