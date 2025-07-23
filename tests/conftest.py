import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from db.db import Base, get_db
from main import app
from fastapi.testclient import TestClient
from config import test_settings
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(
        test_settings.DATABASE_URL, poolclass=NullPool, echo=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session_factory(async_engine):
    return async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )


@pytest.fixture
async def db_session(async_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
def client(async_session_factory):
    async def override_get_db():
        async with async_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_batch_data():
    """Фикстура для тестовых данных партий"""

    return {
        "task_description": "Тестовая партия",
        "work_center": "Участок1",
        "shift": "Дневная",
        "team": "Бригада1",
        "batch_number": 3,
        "batch_date": "2025-07-04",
        "nomenclature": "Товар1",
        "ekn_code": "EKN1",
        "work_center_id": "WC1",
        "shift_start_datetime": "2025-07-05T20:28:51.450Z",
        "shift_end_datetime": "2025-07-05T20:28:51.450Z",
    }


@pytest.fixture
def test_product_data():
    """ "Фикстура для тестовых данных продукта"""

    return {
        "products": [
            {"batch_date": "2025-07-04", "batch_number": 3, "unique_code": "PRD-001"}
        ]
    }
