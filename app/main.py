import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.errors import (
    http_exception_handler, 
    unhandled_exception_handler, 
    validation_exception_handler,
)

from app.routers import auth, bookmarks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

app = FastAPI(title="Bookmarks API")

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(auth.router)
app.include_router(bookmarks.router)
