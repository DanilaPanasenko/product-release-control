from datetime import date

from fastapi import FastAPI, Depends, HTTPException, Query
from starlette import status

from core.logger import logger
from crud.crud_batch import BatchCrud, ProductCrud
from dependencies.product_control import get_batch_creator, get_product_creator
from sсhemas.product_control import (
    BatchCreate,
    Batch,
    ProductCreate,
    ProductResponse,
    BatchAndProduct,
    BatchUpdate,
    BatchFilter,
    BatchAggregation,
)

app = FastAPI()


@app.post("/add_batch/", response_model=Batch)
async def create_batch(
    batch_data: BatchCreate, crud: BatchCrud = Depends(get_batch_creator)
) -> Batch:
    """Эндпоинт создания сменного задания"""

    try:
        logger.info(
            f"Создание сменного задания с номером:{batch_data.batch_number} и датой:{batch_data.batch_date}"
        )
        return await crud.create_batch(batch_data)
    except Exception as e:
        logger.error(f"Ошибка создания сменного задания: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания задания: {str(e)}",
        )


@app.post("/add_product/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate, crud: ProductCrud = Depends(get_product_creator)
) -> ProductResponse:
    """Эндпоинт создания продукта"""
    try:
        logger.info(f"Создание продукта{product_data.products}")
        return await crud.create_product(product_data)
    except HTTPException as e:
        logger.error(f"Ошибка создания продукта{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания продукта: {str(e)}",
        )


@app.get("/get_batch/", response_model=BatchAndProduct)
async def get_batch_id(batch_id: int, crud: BatchCrud = Depends(get_batch_creator)):
    """Эндпоинт для получения сменного задания по id"""
    try:
        logger.info(f"Получения задания с id:{batch_id}")
        return await crud.get_batch(batch_id)
    except HTTPException as e:
        logger.error(f"Не удалось получить задание{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения задания: {str(e)}",
        )


@app.patch("/update/{batch_id}", response_model=BatchUpdate)
async def update_batch_id(
    batch_id: int,
    update_data: BatchUpdate,
    crud: BatchCrud = Depends(get_batch_creator),
):
    """Эндпоинт для обновления задания"""

    update_batch = await crud.update_batch(batch_id, update_data)
    if not update_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Партия с ID: {batch_id} не найдена",
        )
    return update_batch


@app.get("/get_batches/", response_model=list[Batch])
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
    crud: BatchCrud = Depends(get_batch_creator),
):
    """Эндпоинт для получения заданий с фильтрацией"""

    filters = BatchFilter(
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

    try:
        logger.info(f"Задаем фильтр:{filters}")
        batch_filters = await crud.get_batches_filter(filters)
        logger.info(f"Получаем задания по фильтрам:{batch_filters}")
        return batch_filters
    except HTTPException as e:
        logger.error(f"Ошибка получения списка заданий:{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Партия с параметрами: {filters} не найдена",
        )


@app.post("/aggregate_product/", status_code=status.HTTP_200_OK)
async def aggregate_product(
    request: BatchAggregation, crud: ProductCrud = Depends(get_product_creator)
):
    """Агрегирует продукт с указанным уникальным кодом для заданной партии"""

    try:
        logger.info(f"Вносим изменения в задание:{request.batch_id}")
        return await crud.aggregation(request.batch_id, request.unique_code)
    except HTTPException as e:
        logger.error(f"Не удалось внести изменения:{str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Партия с номером: {request.batch_id} не найдена",
        )
