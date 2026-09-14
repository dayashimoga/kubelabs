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


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("apps.api.src.main:app", host="0.0.0.0", port=8000, reload=True)
