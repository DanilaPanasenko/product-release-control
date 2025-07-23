from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Body, HTTPException, Query, Path
from starlette import status

from dependencies.product_control import get_batch_controller, get_product_controller
from presentation.controllers_batch import BatchController
from presentation.controllers_product import ProductController
from sсhemas.product_control import (
    BatchCreate,
    Batch,
    ProductResponse,
    ProductCreate,
    BatchAndProduct,
    BatchResponse,
    CloseBatchCommand,
    UpdateBatchDescriptionCommand,
    UpdateWorkCenterCommand,
    UpdateBatchScheduleCommand,
    BatchFilter,
    BatchAggregation,
)

router = APIRouter(prefix="/api/v1/batches", tags=["batches"])


@router.post("/", response_model=Batch, status_code=201)
async def create_batch(
    batch_data: BatchCreate,
    controller: Annotated[
        BatchController, Depends(get_batch_controller)
    ],  # Явная типизация
) -> Batch:
    return await controller.create_batch(batch_data)


@router.post("/create_product", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    controller: Annotated[ProductController, Depends(get_product_controller)],
):
    return await controller.create_product(product_data)


@router.get("/{batch_id}", response_model=BatchAndProduct)
async def get_batch(
    batch_id: Annotated[int, Path(gt=0, description="ID партии")],
    controller: Annotated[BatchController, Depends(get_batch_controller)],
) -> BatchAndProduct:
    """Эндпоинт для получения сменного задания по id"""

    return await controller.get_batch(batch_id)


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    command_type: str = Body(
        ...,
        description="Тип команды: close, description, work_center, schedule",
        examples=["close", "description", "work_center", "schedule"],
    ),
    command_data: dict = Body(
        ...,
        description="Данные команды в соответствии с её типом",
        examples=[
            {"batch_id": 1, "is_closed": True},
            {"batch_id": 1, "task_description": "Новое описание"},
            {"batch_id": 1, "work_center": "Цех 1", "work_center_id": "wh1"},
            {
                "batch_id": 1,
                "shift_start_datetime": "2023-01-01T08:00:00+03:00",
                "shift_end_datetime": "2023-01-01T20:00:00+03:00",
            },
        ],
    ),
    controller: BatchController = Depends(get_batch_controller),
):
    """
    Обновление сменного задания
    Поддерживает разные типы обновлений через единый endpoint.
    """

    if command_type == "close":
        command = CloseBatchCommand(**command_data)
    elif command_type == "description":
        command = UpdateBatchDescriptionCommand(**command_data)
    elif command_type == "work_center":
        command = UpdateWorkCenterCommand(**command_data)
    elif command_type == "schedule":
        command = UpdateBatchScheduleCommand(**command_data)
    else:
        raise HTTPException(400, detail="Неподдерживаемый тип команды")

    return await controller.update_batch(command)


@router.get("/", response_model=list[Batch])
async def get_batches(
    is_closed: bool | None = Query(None),
    work_center: str | None = Query(None),
    shift: str | None = Query(None),
    team: str | None = Query(None),
    batch_number: int | None = Query(None),
    batch_date: date | None = Query(None),
    work_center_id: str | None = Query(None),
    limit: int | None = Query(10, ge=1),
    offset: int | None = Query(0, ge=0),
    controller: BatchController = Depends(get_batch_controller),
):
    """Эндпоинт для получения заданий с фильтрацией"""

    # Создаем объект фильтра
    batch_filter = BatchFilter(
        is_closed=is_closed,
        work_center=work_center,
        shift=shift,
        team=team,
        batch_number=batch_number,
        batch_date=batch_date,
        work_center_id=work_center_id,
        limit=limit,
        offset=offset,
    )

    return await controller.get_batches_filter(batch_filter)


@router.post("/aggregate_product", status_code=status.HTTP_200_OK)
async def aggregate_product(
    request: BatchAggregation,
    controller: Annotated[ProductController, Depends(get_product_controller)],
):
    """Агрегирует продукт с указанным уникальным кодом для заданной партии"""

    return await controller.aggregation(request.batch_id, request.unique_code)
