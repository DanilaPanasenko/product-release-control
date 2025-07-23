from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases import ProductUseCases
from exceptions.exceptions import handle_controllers_errors, ErrorMessages
from infrastructure.repositories import ProductRepository
from interfaces.product_controllers_interfaces import AbstractProductControllers
from sсhemas.product_control import ProductCreate


class ProductController(AbstractProductControllers):
    def __init__(self, session: AsyncSession):  # Принимаем session вместо use_cases
        self.session = session

    @handle_controllers_errors(ErrorMessages.PRODUCT_CREATE_ERROR)
    async def create_product(self, product_data: ProductCreate) -> dict:
        async with self.session.begin():
            repo = ProductRepository(self.session)
            use_cases = ProductUseCases(repo)
            return await use_cases.create_product(product_data)

    @handle_controllers_errors(ErrorMessages.AGGREGATION_PRODUCT_ERROR)
    async def aggregation(self, batch_id: int, unique_code: str):
        """Агрегация продукта"""

        async with self.session.begin():
            repo = ProductRepository(self.session)
            use_cases = ProductUseCases(repo)
            return await use_cases.aggregation(batch_id, unique_code)
