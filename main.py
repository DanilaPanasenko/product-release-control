from fastapi import FastAPI, HTTPException
from exceptions.exception_handlers import (
    http_exception_handler,
    general_exception_handler,
)
from routers import batch_router

app = FastAPI()

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(
    batch_router.router,
)
