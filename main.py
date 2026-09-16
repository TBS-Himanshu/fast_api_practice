from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from auth.routers import router
from items.routers import router as item_router
from logs.router import router as log_router
# from items.cron import lifespan
from utils import response
from logs.config import logger
from logs.middleware import LoggingMiddleware

from database import Base, engine
import auth.models as models
from fastapi.staticfiles import StaticFiles
from config import settings
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(router)
app.include_router(item_router)
app.include_router(log_router)
@app.get('/test')
def test_api():
    return {
        "status": 200,
        "message": 'Test API is working !!'
    }
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(LoggingMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS.split(','))
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS.split(','),
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_headers=settings.ALLOW_METHODS.split(','),
    allow_methods=settings.ALLOW_METHODS.split(',')
)

@app.exception_handler(RequestValidationError)
async def validation_exceptional_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0]
    field = first_error["loc"][-1]
    message = first_error["msg"]
    return response(status=422, message=f"Invalid value for '{field}': {message}", error=str(errors))
