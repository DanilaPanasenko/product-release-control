from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from application.use_cases import BatchUseCases
from db.db import get_db
from infrastructure.repositories import BatchRepository
from presentation.controllers_batch import BatchController
from presentation.controllers_product import ProductController


def get_batch_controller(session: AsyncSession = Depends(get_db)) -> BatchController:
    repo = BatchRepository(session)
    use_cases = BatchUseCases(repo)
    return BatchController(use_cases)


def get_product_controller(
    session: AsyncSession = Depends(get_db),
) -> ProductController:
    return ProductController(session)
