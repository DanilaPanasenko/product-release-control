from functools import wraps
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from core.logger import logger


class ErrorMessages:
    PRODUCT_NOT_FOUND = "Продукт не найден"
    BATCH_NOT_FOUND = "Партия не найдена ID:"
    INVALID_BATCH_ID = "ID партии должен быть положительным целым числом"
    BATCH_ID_IS_NOT_NONE = "ID не может быть None"
    BATCH_RECEIPT_ERROR = "Ошибка получения партии"
    BATCH_LIST_RECEIPT_ERROR = "Ошибка при получении списка партий:"
    BATCH_UPDATE_ERROR = "Ошибка обновления партии"
    BAD_REQUEST = "Ошибка формирования запроса"
    BAD_REQUEST_CODE = "Ошибка проверки существующих кодов"
    AGGREGATION_PRODUCT_ERROR = "Ошибка агрегации продукта"
    BATCH_ALREADY_EXISTS = "Партия уже сущесвтует:"
    PRODUCT_CREATE_ERROR = "Ошибка при создании продуктов"
    BATCH_CREATE_ERROR = "Ошибка создания партии"
    ANOTHER_BATCH = "Уникальный код прикреплен к другой партии"
    COD_ALREADY_USED = "Уникальный код, который уже использовался на"


class StatusCodes:
    BAD_REQUEST = 400
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_ERROR = 500


def handle_db_errors(msg):
    """
    Декоратор для 500 ошибки
    :param msg: Сообщения ErrorMessages
    :return: decorator
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"{msg}:{str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=StatusCodes.INTERNAL_ERROR, detail=f"{msg}:{str(e)}"
                )

        return wrapper

    return decorator


def handle_controllers_errors(msg):
    """
    Декоратор для ошибок валидации и 500
    :param msg: Сообщения ErrorMessages
    :return: decorator
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValidationError as ve:
                logger.error(f"{msg}:{str(ve)}", exc_info=True)
                raise HTTPException(
                    status_code=StatusCodes.UNPROCESSABLE_ENTITY,
                    detail={
                        "type": "validation_error",
                        "errors": ve.errors(),
                        "message": "Ошибка валидации входных данных",
                    },
                )
            except SQLAlchemyError as e:
                logger.error(f"{msg}:{str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=StatusCodes.INTERNAL_ERROR, detail=f"{msg}:{str(e)}"
                )

        return wrapper

    return decorator
