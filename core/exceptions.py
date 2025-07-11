from fastapi import HTTPException, status


class BatchNotFoundError(HTTPException):
    def __init__(self, batch_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Задание с ID {batch_id} не найдено",
        )


class ExternalApiError(HTTPException):
    def __init__(self, api_name: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Сервис {api_name} недоступен",
        )
