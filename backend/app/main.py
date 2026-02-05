import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import async_session
from app.api.v1.router import api_router
from app.services.market_seed import seed_market_data

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: seed market data
    try:
        async with async_session() as db:
            count = await seed_market_data(db)
            if count > 0:
                logger.info(f"Seeded {count} market data entries")
    except Exception as e:
        logger.warning(f"Market data seed skipped: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
