import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.routers import (
    health, overview, plants, machines, safety_zones,
    alarms, incidents, anomalies, corrective_actions,
    metrics, data_quality, generation, export
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("industrial_safety")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Industrial Safety Intelligence Platform...")
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified.")
    yield
    logger.info("Shutting down Industrial Safety Intelligence Platform...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Industrial Safety Event Analysis, Traceability, and Anomaly Detection Platform.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)}
    )

# Include Routers under /api
app.include_router(health.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(plants.router, prefix="/api")
app.include_router(machines.router, prefix="/api")
app.include_router(safety_zones.router, prefix="/api")
app.include_router(alarms.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(anomalies.router, prefix="/api")
app.include_router(corrective_actions.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(data_quality.router, prefix="/api")
app.include_router(generation.router, prefix="/api")
app.include_router(export.router, prefix="/api")

@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_prefix": "/api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
