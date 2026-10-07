from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.routes import certificates

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="A backend API for generating bulk PDF certificates for events and courses.",
)

# Include routers
app.include_router(certificates.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred."},
    )


@app.get("/health", tags=["Health"])
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
