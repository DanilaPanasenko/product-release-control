from abc import ABC, abstractmethod

from sсhemas.product_control import ProductCreate


class AbstractProductControllers(ABC):
    @abstractmethod
    async def create_product(self, product_data: ProductCreate) -> dict:
        pass

    @abstractmethod
    async def aggregation(self, batch_id: int, unique_code: str):
        pass
