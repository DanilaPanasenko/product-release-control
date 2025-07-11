from datetime import date, datetime, timezone
from typing import List
from pydantic import BaseModel, field_validator, Field, ConfigDict


class BatchBase(BaseModel):
    """Базовая pydantic схема для задания"""

    task_description: str
    work_center: str
    shift: str
    team: str
    batch_number: int
    batch_date: date
    nomenclature: str
    ekn_code: str
    work_center_id: str
    shift_start_datetime: datetime
    shift_end_datetime: datetime


class BatchCreate(BatchBase):
    """Схема для создания задания"""

    @field_validator("shift_start_datetime", "shift_end_datetime")
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    model_config = ConfigDict(extra="forbid")


class Batch(BatchBase):
    """Полная схема с ID для задания"""

    id: int
    is_closed: bool
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    """Базовая схема продукта"""

    unique_code: str = Field(
        description="Уникальный код продукта",
        json_schema_extra={"example": "Prd-123-ABC"},
        min_length=5,
        max_length=20,
    )
    batch_number: int = Field(
        description="Номер партии", json_schema_extra={"example": 12345}, gt=0
    )
    batch_date: date = Field(
        description="Дата производства в формате YYYY-MM-DD",
        json_schema_extra={"example": "2025-05-20"},
    )


class ProductCreate(BaseModel):
    """Схема создания списка продукта"""

    products: List[ProductBase] = Field(
        description="Список продуктов",
        json_schema_extra={
            "example": [
                {
                    "unique_code": "PRD-001",
                    "batch_number": 123,
                    "batch_date": "2025-05-22",
                }
            ]
        },
    )


class ProductResponse(BaseModel):
    added: int
    skipped_existing: int
    skipped_invalid_batch: int


class ProductInBatch(BaseModel):
    """Схема для продуктов в составе партии"""

    unique_code: str
    is_aggregated: bool
    aggregated_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchAndProduct(Batch):
    products: List[ProductInBatch]

    model_config = ConfigDict(from_attributes=True)


class BatchUpdate(BaseModel):
    """Схема для обновления партии"""

    is_closed: bool | None = None
    task_description: str | None = None
    work_center: str | None = None
    shift: str | None = None
    team: str | None = None
    batch_number: int | None = None
    batch_date: date | None = None
    nomenclature: str | None = None
    ekn_code: str | None = None
    work_center_id: str | None = None
    shift_start_datetime: datetime | None = None
    shift_end_datetime: datetime | None = None

    @field_validator("is_closed")
    def set_closed_at(cls, v):
        """Валидация поля is_closed"""

        if v is not None:
            return {"is_closed": v, "closed_at": datetime.now() if v else None}
        return v


class BatchFilter(BaseModel):
    """Схема фильтрации заданий"""

    is_closed: bool | None = None
    work_center: str | None = None
    shift: str | None = None
    team: str | None = None
    batch_number: int | None = None
    batch_date: date | None = None
    work_center_id: str | None = None
    limit: int | None = 10
    offset: int | None = None

    model_config = ConfigDict(extra="forbid")


class BatchAggregation(BaseModel):
    """Схема агрегации"""

    batch_id: int
    unique_code: str
