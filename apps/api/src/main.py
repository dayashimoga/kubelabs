"""
KubeLabs API Entrypoint.
Production-ready FastAPI Modular Monolith.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import engine, Base
from .api import labs, incidents, assessments, dashboard, telemetry, terminal


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas on startup
    Base.metadata.create_all(bind=engine)
    print(f"[{settings.PROJECT_NAME}] Initialized database schema.")
    yield
    print(f"[{settings.PROJECT_NAME}] Shutting down cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-Ready DevOps & SRE Hands-on Learning, Troubleshooting & Incident Simulation Platform",
    lifespan=lifespan,
)

# Enable CORS for local dev and frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import uuid
from fastapi import Response, status
from .core.database import check_db_health
from .core.redis_manager import redis_manager


@app.middleware("http")
async def add_request_id_and_security_headers(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Register Routers
app.include_router(labs.router, prefix=settings.API_V1_STR)
app.include_router(incidents.router, prefix=settings.API_V1_STR)
app.include_router(assessments.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(terminal.router)


@app.get("/healthz")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/readyz")
def readiness_check(response: Response):
    db_ok = check_db_health()
    redis_ok = redis_manager.check_health()
    ready = db_ok and redis_ok

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "ready": ready,
        "components": {
            "database": "connected" if db_ok else "unreachable",
            "redis_cache": "connected" if redis_ok else "degraded",
            "podman_sandbox": "available" if settings.ENABLE_PODMAN else "simulation_only",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.src.main:app", host="0.0.0.0", port=8000, reload=True)
