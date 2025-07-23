from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from sсhemas.product_control import (
    Batch,
    BatchAndProduct,
    BatchFilter,
    BaseBatchCommand,
    BatchResponse,
)


class AbstractBatchControllers(ABC):
    @abstractmethod
    async def create_batch(self, batch_data) -> Batch:
        pass

    @abstractmethod
    async def get_batch(self, batch_id: int) -> Optional[BatchAndProduct]:
        pass

    @abstractmethod
    async def update_batch(self, command: BaseBatchCommand) -> BatchResponse:
        pass

    @abstractmethod
    async def get_batches_filter(
        self, batch_filter: BatchFilter
    ) -> List[Dict[str, Any]]:
        pass
