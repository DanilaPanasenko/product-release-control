from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from exceptions.exceptions import StatusCodes, ErrorMessages, handle_db_errors
from infrastructure.repositories import BatchRepository, ProductRepository
from models.product_control import BatchModel, ProductModel
from sсhemas.product_control import (
    BatchCreate,
    ProductCreate,
    BatchAndProduct,
    Batch,
    BatchFilter,
    BaseBatchCommand,
    CloseBatchCommand,
    UpdateBatchDescriptionCommand,
    UpdateWorkCenterCommand,
    UpdateBatchScheduleCommand,
)


class BatchUseCases:
    def __init__(self, repo: BatchRepository):
        self.repo = repo

    async def create_batch(self, batch_data: BatchCreate) -> Batch:
        if await self.repo.exists(batch_data.batch_number, batch_data.batch_date):
            raise HTTPException(
                status_code=StatusCodes.BAD_REQUEST,
                detail=f"{ErrorMessages.BATCH_ALREADY_EXISTS}{batch_data.batch_number};{batch_data.batch_date}",
            )

        batch_model = await self.repo.create(batch_data)
        return Batch.model_validate(batch_model)

    async def get_batch(self, batch_id: int) -> Optional[BatchAndProduct]:
        try:
            # Валидация базовых случаев
            if batch_id is None:
                raise HTTPException(
                    status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                    detail=ErrorMessages.BATCH_ID_IS_NOT_NONE,
                )

            if batch_id <= 0:
                raise HTTPException(
                    status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                    detail=ErrorMessages.INVALID_BATCH_ID,
                )

            # Получаем данные
            batch = await self.repo.get_by_id(batch_id)

            if not batch:
                raise HTTPException(
                    status_code=StatusCodes.NOT_FOUND,
                    detail=ErrorMessages.BATCH_NOT_FOUND,
                )

            # Валидация через Pydantic
            return BatchAndProduct.model_validate(batch)

        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail={"message": "Ошибка валидации данных", "errors": e.errors()},
            )
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=500, detail=f"Ошибка при получении партии: {str(e)}"
            )

    @handle_db_errors(ErrorMessages.BATCH_UPDATE_ERROR)
    async def update_batch(self, command: BaseBatchCommand) -> BatchModel:
        if command.batch_id is None:
            raise HTTPException(
                status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                detail=ErrorMessages.BATCH_ID_IS_NOT_NONE,
            )

        if command.batch_id <= 0:
            raise HTTPException(
                status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                detail=ErrorMessages.INVALID_BATCH_ID,
            )
        update_values = {}

        if isinstance(command, CloseBatchCommand):
            update_values.update(
                {
                    "is_closed": command.is_closed,
                    "closed_at": datetime.now() if command.is_closed else None,
                }
            )
        elif isinstance(command, UpdateBatchDescriptionCommand):
            update_values["task_description"] = command.task_description
        elif isinstance(command, UpdateWorkCenterCommand):
            update_values.update(
                {
                    "work_center": command.work_center,
                    "work_center_id": command.work_center_id,
                }
            )
        elif isinstance(command, UpdateBatchScheduleCommand):
            update_values.update(
                {
                    "shift_start_datetime": command.shift_start_datetime,
                    "shift_end_datetime": command.shift_end_datetime,
                }
            )

        updated_batch = await self.repo.update_batch(command.batch_id, update_values)
        if not updated_batch:
            raise HTTPException(
                status_code=StatusCodes.NOT_FOUND, detail=ErrorMessages.BATCH_NOT_FOUND
            )
        return updated_batch

    @handle_db_errors(ErrorMessages.BATCH_LIST_RECEIPT_ERROR)
    async def get_batches_filter(
        self, batch_filter: BatchFilter
    ) -> List[Dict[str, Any]]:
        query = await self.repo.get_batch_filter(batch_filter)
        result = await self.repo.execute_query(query)
        return result


class ProductUseCases:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    @handle_db_errors(ErrorMessages.PRODUCT_CREATE_ERROR)
    async def create_product(self, product_data: ProductCreate) -> dict:
        """Бизнес-логика создания продукта с пакетной обработкой"""

        result = {
            "added": 0,
            "skipped": 0,
            "skipped_existing": 0,
            "skipped_invalid_batch": 0,
        }

        # Получаем все unique_codes из запроса
        unique_codes = [item.unique_code for item in product_data.products]

        # 1. Проверяем существующие продукты одним запросом
        existing_codes = await self.repo.get_existing_product_codes(unique_codes)
        result["skipped_existing"] = len(existing_codes)

        # Фильтруем только новые продукты
        new_products = [
            item
            for item in product_data.products
            if item.unique_code not in existing_codes
        ]

        if not new_products:
            return result

        # 2. Получаем все нужные партии одним запросом
        batch_details = {(item.batch_number, item.batch_date) for item in new_products}
        batches = await self.repo.get_batches_by_details(batch_details)

        # 3. Группируем продукты по валидным партиям
        products_to_create = []
        for item in new_products:
            batch_key = (item.batch_number, item.batch_date)
            if batch_key in batches:
                products_to_create.append((item, batches[batch_key]))
            else:
                result["skipped_invalid_batch"] += 1

        if not products_to_create:
            return result

        # 4. Пакетное создание продуктов (исправленная часть)
        product_models = [
            ProductModel(
                unique_code=item.unique_code,
                batch_id=batch_id,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            for item, batch_id in products_to_create
        ]

        await self.repo.bulk_create_products(product_models)
        result["added"] = len(products_to_create)
        return result

    @handle_db_errors(ErrorMessages.AGGREGATION_PRODUCT_ERROR)
    async def aggregation(self, batch_id: int, unique_code: str) -> dict:
        """Бизнес-логика агрегации продукта"""

        product = await self.repo.aggregation(unique_code)

        if not product:
            raise HTTPException(
                status_code=StatusCodes.NOT_FOUND,
                detail=ErrorMessages.PRODUCT_NOT_FOUND,
            )

        # Проверяем привязку к партии
        if product.batch_id != batch_id:
            raise HTTPException(
                status_code=StatusCodes.BAD_REQUEST,
                detail=ErrorMessages.ANOTHER_BATCH,
            )

        # Проверяем, не был ли уже агрегирован
        if product.is_aggregated:
            raise HTTPException(
                status_code=StatusCodes.BAD_REQUEST,
                detail=f"{ErrorMessages.COD_ALREADY_USED} {product.aggregated_at}",
            )

        # Обновляем запись
        product.is_aggregated = True
        product.aggregated_at = datetime.now()

        return {
            "unique_code": product.unique_code,
            "batch_id": product.batch_id,
            "aggregated_at": product.aggregated_at,
        }
