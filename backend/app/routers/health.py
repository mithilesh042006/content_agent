"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Basic health check — confirms the service is running."""
    return {
        "status": "healthy",
        "service": "strategent-ai",
        "version": "1.0.0",
    }
