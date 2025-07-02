from datetime import date, datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.sql.schema import UniqueConstraint
from db.db import Base


class BatchModel(Base):
    """Главная модель для работы с заданиями"""

    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_closed: Mapped[bool] = mapped_column(comment="Статус закрытия", default=False)
    task_description: Mapped[str] = mapped_column(comment="Описание здания")
    work_center: Mapped[str] = mapped_column(comment="Участок на производстве")
    shift: Mapped[str] = mapped_column(comment="Смена")
    team: Mapped[str] = mapped_column(comment="Бригада")
    batch_number: Mapped[int] = mapped_column(comment="Номер партии")
    batch_date: Mapped[date] = mapped_column(comment="Дата партии")
    nomenclature: Mapped[str] = mapped_column(comment="Номенклатура")
    ekn_code: Mapped[str] = mapped_column(comment="КодЕКН")
    work_center_id: Mapped[str] = mapped_column(comment="ИдентификаторРЦ")
    shift_start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата время начала смены"
    )
    shift_end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), comment="Дата время конца смены"
    )
    closed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        comment="Дата закрытия партии",
        nullable=True,  # Явно разрешаем NULL
        server_default=None,  # Указываем явно None вместо null()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="Дата создания записи"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата обновления",
    )

    products = relationship(
        "ProductModel", back_populates="batch", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("batch_number", "batch_date", name="uix_batch_number_date"),
    )


class ProductModel(Base):
    """Главная модель для работы с продуктом"""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    unique_code: Mapped[str] = mapped_column(
        unique=True, comment="Уникальный код продукта"
    )
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    is_aggregated: Mapped[bool] = mapped_column(default=False, comment="Флаг агрегации")
    aggregated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, comment="Дата агрегации"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="дата создания записи"
    )

    batch = relationship("BatchModel", back_populates="products")
