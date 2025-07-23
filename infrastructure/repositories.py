from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, exists
from sqlalchemy.orm import selectinload

from exceptions.exceptions import handle_db_errors, ErrorMessages, StatusCodes
from models.product_control import BatchModel, ProductModel
from sсhemas.product_control import BatchCreate, BatchAndProduct, BatchFilter


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, batch_number: int, batch_date: date) -> bool:
        """
        Запрос к бд для проверки налиячия партии
        :param batch_number: номер партии
        :param batch_date: дата создания партии
        """

        result = await self.session.execute(
            select(BatchModel).where(
                (BatchModel.batch_number == batch_number)
                & (BatchModel.batch_date == batch_date)
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(self, batch_data: BatchCreate) -> BatchModel:
        try:
            batch = BatchModel(**batch_data.model_dump())
            self.session.add(batch)
            await self.session.commit()
            await self.session.refresh(batch)
            return batch
        except IntegrityError as e:
            await self.session.rollback()
            if "uix_batch_number_date" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Партия с таким номером и датой уже существует",
                )
            raise HTTPException(
                status_code=400, detail=f"Ошибка целостности данных: {str(e)}"
            )

    @handle_db_errors(ErrorMessages.BATCH_RECEIPT_ERROR)
    async def get_by_id(self, batch_id: int):
        if not isinstance(batch_id, int) or batch_id <= 0:
            raise HTTPException(
                status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                detail=ErrorMessages.INVALID_BATCH_ID,
            )
        async with self.session.begin():
            result = await self.session.execute(
                select(BatchModel)
                .where(BatchModel.id == batch_id)
                .options(selectinload(BatchModel.products))
            )
            batch = result.scalar_one_or_none()
            if not batch:
                raise HTTPException(
                    status_code=StatusCodes.NOT_FOUND,
                    detail=f"{ErrorMessages.BATCH_NOT_FOUND}{batch_id}",
                )
            return BatchAndProduct.model_validate(batch)

    @handle_db_errors(ErrorMessages.BATCH_UPDATE_ERROR)
    async def update_batch(
        self, batch_id: int, update_data: dict
    ) -> Optional[BatchModel]:
        if not isinstance(batch_id, int) or batch_id <= 0:
            raise HTTPException(
                status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                detail=ErrorMessages.INVALID_BATCH_ID,
            )

        async with self.session.begin():
            if not update_data:
                return await self.session.get(BatchModel, batch_id)

            result = await self.session.execute(
                update(BatchModel)
                .where(BatchModel.id == batch_id)
                .values(**update_data)
                .returning(BatchModel)
            )
            return result.scalar_one_or_none()

    @handle_db_errors(ErrorMessages.BAD_REQUEST)
    async def get_batch_filter(self, batch_filter: BatchFilter):
        async with self.session.begin():
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

            return query

    @handle_db_errors(ErrorMessages.BAD_REQUEST)
    async def execute_query(self, query):
        result = await self.session.execute(query)
        return result.scalars().all()


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @handle_db_errors(ErrorMessages.BAD_REQUEST_CODE)
    async def get_existing_product_codes(self, codes: list[str]) -> set[str]:
        """
        Возвращает множество существущих unique_code
        :param codes: список unique_code
        """

        if not codes:
            return set()

        result = await self.session.execute(
            select(ProductModel.unique_code).where(ProductModel.unique_code.in_(codes))
        )
        return {row[0] for row in result.all()}

    @handle_db_errors(ErrorMessages.BATCH_RECEIPT_ERROR)
    async def get_batches_by_details(
        self, details: set[tuple[int, date]]
    ) -> dict[tuple[int, date], int]:
        """Возвращает словарь {(batch_number, batch_date): batch_id}"""

        if not details:
            return {}
        batch_numbers, batch_dates = zip(*details)
        result = await self.session.execute(
            select(BatchModel.batch_number, BatchModel.batch_date, BatchModel.id).where(
                (BatchModel.batch_number.in_(batch_numbers))
                & (BatchModel.batch_date.in_(batch_dates))
            )
        )
        return {(row[0], row[1]): row[2] for row in result.all()}

    async def bulk_create_products(self, products: list[ProductModel]):
        """Массовая вставка продуктов с обработкой ошибок"""
        if not products:
            return

        try:
            self.session.add_all(products)
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=409, detail=f"Конфликт уникальных кодов продуктов: {str(e)}"
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise HTTPException(
                status_code=500, detail=f"Ошибка массового создания продуктов: {str(e)}"
            )

    @handle_db_errors(ErrorMessages.BATCH_RECEIPT_ERROR)
    async def product_exists(self, unique_code: str) -> bool:
        """Оставлено для обратной совместимости"""

        result = await self.session.execute(
            select(exists().where(ProductModel.unique_code == unique_code))
        )
        return result.scalar()

    @handle_db_errors(ErrorMessages.AGGREGATION_PRODUCT_ERROR)
    async def aggregation(self, unique_code: str):
        result = await self.session.execute(
            select(ProductModel).where(ProductModel.unique_code == unique_code)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=StatusCodes.NOT_FOUND,
                detail=f"{ErrorMessages.PRODUCT_NOT_FOUND}, код: {unique_code}",
            )
