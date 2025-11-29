from fastapi import FastAPI
from app.routers import finance, economics
from app.core.logging import configure_logging
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from app.config import settings
from redis import asyncio as aioredis
import structlog

configure_logging()
logger = structlog.get_logger()

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

@app.on_event("startup")
async def startup():
    try:
        redis = aioredis.from_url(settings.REDIS_URL)
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        logger.info("Initialized Redis cache")
    except Exception as e:
        logger.warning(f"Redis not available, using InMemory cache: {e}")
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

app.include_router(finance.router, prefix="/api", tags=["Finance"])
app.include_router(economics.router, prefix="/api", tags=["Economics"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Finance Data Aggregator API"}