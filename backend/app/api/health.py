import time
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Liveness check returning current status and version."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get("/health/gemini")
def gemini_health_check():
    """Check Gemini API configuration and reachability."""
    if not settings.has_gemini_key:
        return {
            "status": "unconfigured",
            "message": "GEMINI_API_KEY is not set or using placeholder.",
            "flash_model": settings.GEMINI_FLASH_MODEL,
            "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
        }

    start = time.perf_counter()
    try:
        # Use cached configuration from gemini_client
        from app.services.gemini_client import _ensure_genai_configured
        _ensure_genai_configured()
        import google.generativeai as genai
        model = genai.GenerativeModel(settings.GEMINI_FLASH_MODEL)
        response = model.generate_content("ping", request_options={"timeout": 5})
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "ok",
            "latency_ms": latency_ms,
            "model": settings.GEMINI_FLASH_MODEL,
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "error",
            "latency_ms": latency_ms,
            "error": str(e),
        }
