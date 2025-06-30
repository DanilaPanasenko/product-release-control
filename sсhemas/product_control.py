from datetime import date, datetime, timezone
from typing import List

from pydantic import BaseModel, field_validator


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

    @field_validator('shift_start_datetime', 'shift_end_datetime')
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config:
        extra = "forbid"


class Batch(BatchBase):
    """Полная схема с ID для задания"""

    id: int
    is_closed: bool
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ProductBase(BaseModel):
    """Базовая схема продукта"""

    unique_code: str
    batch_number: int
    batch_date: date


class ProductCreate(BaseModel):
    """Схема создания списка продукта"""

    products: List[ProductBase]


class ProductResponse(BaseModel):
    added: int
    skipped_existing: int
    skipped_invalid_batch: int
