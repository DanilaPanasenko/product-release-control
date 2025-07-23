from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator, Field, ConfigDict, model_validator


class BatchBase(BaseModel):

    task_description: str = Field(
        min_length=1, max_length=500, description="Описание задания"
    )
    work_center: str = Field(
        min_length=1, max_length=100, description="Название рабочего центра"
    )
    shift: str = Field(pattern=r"^[A-C]$", description="Наименования смены")
    team: str = Field(min_length=1, max_length=50, description="Имя команды")
    batch_number: int = Field(gt=0, le=999999, description="Номер партии")
    batch_date: date = Field(
        le=date.today(), description="Дата производства в формате YYYY-MM-DD"
    )
    nomenclature: str = Field(
        min_length=1, max_length=200, description="Названия продукта"
    )
    ekn_code: str = Field(pattern=r"^[A-Z0-9]{6,12}$")
    work_center_id: str = Field(
        min_length=1, max_length=20, description="Идентификатор рабочего центра"
    )
    shift_start_datetime: datetime = Field(description="Дата и время начала смены")
    shift_end_datetime: datetime = Field(description="Дата и время окончания смены")


class BatchCreate(BatchBase):
    """
    Команда для создания новой партии производства.

    Содержит все необходимые данные для создания сменного задания,
    включая временные рамки смены и привязку к рабочему центру.
    """

    model_config = ConfigDict(extra="forbid")

    @field_validator("shift_start_datetime", "shift_end_datetime")
    @classmethod
    def validate_timezone_required(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Timezone is required")
        return v

    @model_validator(mode="after")
    def validate_shift_times(self):
        if self.shift_start_datetime > self.shift_end_datetime:
            raise ValueError("Время начала смены должно быть раньше окончания")

        # Проверка что смена не больше 24 часов
        if (
            self.shift_end_datetime - self.shift_start_datetime
        ).total_seconds() > 24 * 3600:
            raise ValueError("Смена не может длиться более 24 часов")

        return self


class Batch(BatchBase):
    """Полная схема с ID для задания"""

    id: int = Field(gt=0, description="ID должен быть положительным числом")
    is_closed: bool = Field(description="Статус закытия партии")
    closed_at: datetime | None = Field(description="Дата закытия партии")
    created_at: datetime = Field(description="Дата создания партии")
    updated_at: datetime = Field(description="Дата обновления партии")

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):

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
    """
    Схема создания списка продукта, вкдючает в себя уникальный код, номе патии и дату патии
    """

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

    @field_validator("products")
    @classmethod
    def validate_unique_codes(cls, v: List[ProductBase]) -> List[ProductBase]:
        unique_codes = [p.unique_code for p in v]
        if len(unique_codes) != len(set(unique_codes)):
            raise ValueError("Duplicate unique codes found")
        return v


class ProductResponse(BaseModel):
    """
    Схема ответа добавления продукта
    """
    added: int = Field(ge=0, description="Количество добавленных продуктов")
    skipped: int = Field(ge=0, description="Количество пропущенных продуктов")


class ProductInBatch(BaseModel):
    """
    Схема для продуктов в составе партии
    """

    unique_code: str = Field(min_length=1, description="Уникальный код")
    is_aggregated: bool = Field(description="Флаг агрегации")
    aggregated_at: datetime | None = Field(description="Дата агрегации")
    created_at: datetime = Field(description="Дата создания записи")

    model_config = ConfigDict(from_attributes=True)


class BatchAndProduct(Batch):
    products: List[ProductInBatch]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id")
    @classmethod
    def validate_batch_id(cls, v):
        if v is None:
            raise ValueError("ID не может быть None")
        if v <= 0:
            raise ValueError("ID должен быть положительным числом")
        return v


class BatchFilter(BaseModel):
    """
    Схема фильтрации заданий(можно отфильтровать по 1 или нескольким полям)
    """

    is_closed: bool | None = None
    work_center: str | None = Field(default=None, min_length=1, max_length=100)
    shift: str | None = Field(default=None, pattern=r"^[A-C]$")
    team: str | None = Field(default=None, min_length=1, max_length=50)
    batch_number: int | None = Field(default=None, gt=0, le=999999)
    batch_date: date | None = Field(default=None, le=date.today())
    work_center_id: str | None = Field(default=None, min_length=1, max_length=20)
    limit: int | None = Field(default=10, ge=0)
    offset: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")


class BatchAggregation(BaseModel):
    """Схема агрегации"""

    batch_id: int = Field(gt=0)
    unique_code: str = Field(min_length=5, max_length=20)


class BaseBatchCommand(BaseModel):
    """Базовая команда с ID партии"""

    batch_id: int = Field(gt=0, description="ID сменного задания")


class CloseBatchCommand(BaseBatchCommand):
    """Команда закрытия/открытия партии"""

    is_closed: bool = Field(description="Флаг закрытия партии")


class UpdateBatchDescriptionCommand(BaseBatchCommand):
    """Команда обновления описания"""

    task_description: str = Field(
        min_length=1, max_length=500, description="Описание задания"
    )


class UpdateWorkCenterCommand(BaseBatchCommand):
    """Команда обновления рабочего центра"""

    work_center: str = Field(
        min_length=1, max_length=100, description="Название рабочего центра"
    )
    work_center_id: str = Field(
        min_length=1, max_length=20, description="Идентификатор рабочего центра"
    )


class UpdateBatchScheduleCommand(BaseBatchCommand):
    """Команда обновления расписания"""

    shift_start_datetime: datetime = Field(description="Дата и время начала смены")
    shift_end_datetime: datetime = Field(description="Дата и время окончания смены")

    @field_validator("shift_start_datetime", "shift_end_datetime")
    @classmethod
    def validate_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("Требуется указание временной зоны")
        return v

    @model_validator(mode="after")
    def validate_shift_times(self) -> "UpdateBatchScheduleCommand":
        if self.shift_start_datetime >= self.shift_end_datetime:
            raise ValueError("Время начала смены должно быть раньше окончания")
        if (
            self.shift_end_datetime - self.shift_start_datetime
        ).total_seconds() > 24 * 3600:
            raise ValueError("Смена не может длиться более 24 часов")
        return self


class BatchResponse(BaseModel):
    id: int
    is_closed: bool
    closed_at: Optional[datetime] = None
    task_description: str
    work_center: str
    work_center_id: str
    shift: str
    team: str
    batch_number: int
    batch_date: date
    nomenclature: str
    ekn_code: str
    shift_start_datetime: datetime
    shift_end_datetime: datetime

    model_config = ConfigDict(from_attributes=True)
