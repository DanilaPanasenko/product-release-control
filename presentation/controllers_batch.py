from typing import Optional, List, Dict, Any


from application.use_cases import BatchUseCases
from exceptions.exceptions import handle_controllers_errors, ErrorMessages
from interfaces.batch_controllers_interfaces import AbstractBatchControllers
from sсhemas.product_control import (
    Batch,
    BatchAndProduct,
    BatchFilter,
    BaseBatchCommand,
    BatchResponse,
)


class BatchController(AbstractBatchControllers):
    def __init__(self, use_cases: BatchUseCases):  # Принимаем только use_cases
        self.use_cases = use_cases

    @handle_controllers_errors(ErrorMessages.BATCH_CREATE_ERROR)
    async def create_batch(self, batch_data) -> Batch:
        return await self.use_cases.create_batch(batch_data)

    @handle_controllers_errors(ErrorMessages.BATCH_RECEIPT_ERROR)
    async def get_batch(self, batch_id: int) -> Optional[BatchAndProduct]:
        return await self.use_cases.get_batch(batch_id)

    @handle_controllers_errors(ErrorMessages.BATCH_UPDATE_ERROR)
    async def update_batch(self, command: BaseBatchCommand) -> BatchResponse:
        batch_model = await self.use_cases.update_batch(command)
        return BatchResponse.model_validate(batch_model)

    @handle_controllers_errors(ErrorMessages.BATCH_LIST_RECEIPT_ERROR)
    async def get_batches_filter(
        self, batch_filter: BatchFilter
    ) -> List[Dict[str, Any]]:
        return await self.use_cases.get_batches_filter(batch_filter)
