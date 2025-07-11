"""empty message

Revision ID: f63d3d326ecf
Revises:
Create Date: 2025-07-04 15:18:22.099477

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f63d3d326ecf"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "batches",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "is_closed",
            sa.BOOLEAN(),
            nullable=False,
            comment="Статус закрытия",
        ),
        sa.Column(
            "task_description",
            sa.VARCHAR(),
            nullable=False,
            comment="Описание здания",
        ),
        sa.Column(
            "work_center",
            sa.VARCHAR(),
            nullable=False,
            comment="Участок на производстве",
        ),
        sa.Column("shift", sa.VARCHAR(), nullable=False, comment="Смена"),
        sa.Column("team", sa.VARCHAR(), nullable=False, comment="Бригада"),
        sa.Column(
            "batch_number",
            sa.INTEGER(),
            nullable=False,
            comment="Номер партии",
        ),
        sa.Column(
            "batch_date",
            sa.DATE(),
            nullable=False,
            comment="Дата партии",
        ),
        sa.Column(
            "nomenclature",
            sa.VARCHAR(),
            nullable=False,
            comment="Номенклатура",
        ),
        sa.Column(
            "ekn_code",
            sa.VARCHAR(),
            nullable=False,
            comment="КодЕКН",
        ),
        sa.Column(
            "work_center_id",
            sa.VARCHAR(),
            nullable=False,
            comment="ИдентификаторРЦ",
        ),
        sa.Column(
            "shift_start_datetime",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Дата время начала смены",
        ),
        sa.Column(
            "shift_end_datetime",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Дата время конца смены",
        ),
        sa.Column(
            "closed_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Дата закрытия партии",
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания записи",
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата обновления",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("batches_pkey")),
        sa.UniqueConstraint(
            "batch_number", "batch_date", name=op.f("uix_batch_number_date")
        ),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "unique_code",
            sa.VARCHAR(),
            nullable=False,
            comment="Уникальный код продукта",
        ),
        sa.Column("batch_id", sa.INTEGER(), nullable=False),
        sa.Column(
            "is_aggregated",
            sa.BOOLEAN(),
            nullable=False,
            comment="Флаг агрегации",
        ),
        sa.Column(
            "aggregated_at",
            postgresql.TIMESTAMP(),
            nullable=True,
            comment="Дата агрегации",
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="дата создания записи",
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"], ["batches.id"], name=op.f("products_batch_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("products_pkey")),
        sa.UniqueConstraint("unique_code", name=op.f("products_unique_code_key")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("products")
    op.drop_table("batches")
    # ### end Alembic commands ###
