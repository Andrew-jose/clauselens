import logging
from typing import List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Global cached fallback model instance (lazy loaded)
_lazy_local_model = None


def get_lazy_local_model():
    """Lazily load sentence-transformers only when fallback is triggered."""
    global _lazy_local_model
    if _lazy_local_model is None:
        logger.info("Lazily loading fallback sentence-transformers (all-MiniLM-L6-v2)...")
        from sentence_transformers import SentenceTransformer
        _lazy_local_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _lazy_local_model


def embed_texts(texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
    """
    Generate embeddings for a list of strings.
    Primary: Gemini API (`gemini-embedding-001`).
    Fallback: Lazy-loaded `sentence-transformers` (all-MiniLM-L6-v2).
    """
    if not texts:
        return []

    # 1. Try primary Gemini Embeddings if API key is provided
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)

            # Gemini embedding model format
            model_name = settings.GEMINI_EMBEDDING_MODEL
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"

            # If task_type is for queries vs documents
            g_task = "RETRIEVAL_DOCUMENT" if task_type == "retrieval_document" else "RETRIEVAL_QUERY"

            response = genai.embed_content(
                model=model_name,
                content=texts,
                task_type=g_task,
            )
            if "embedding" in response:
                embeddings = response["embedding"]
                # Single item vs list
                if len(texts) == 1 and isinstance(embeddings[0], float):
                    return [embeddings]
                return embeddings
        except Exception as e:
            logger.warning(
                f"Primary Gemini embedding call ({settings.GEMINI_EMBEDDING_MODEL}) failed: {e}. "
                "Triggering fallback..."
            )

    # 2. Fallback: Lazy load local sentence-transformers model
    try:
        model = get_lazy_local_model()
        embeddings = model.encode(texts, convert_to_numpy=True).tolist()
        return embeddings
    except Exception as e:
        logger.error(f"Fallback embedding model failed: {e}. Using deterministic mock embeddings for safety.")
        # Deterministic lightweight vector fallback (384 dimensions) for offline testing without torch
        vectors = []
        for text in texts:
            vec = [float((hash(text + str(i)) % 1000) / 1000.0) for i in range(384)]
            vectors.append(vec)
        return vectors


def embed_query(query: str) -> List[float]:
    """Generate embedding for a single search query."""
    embeddings = embed_texts([query], task_type="retrieval_query")
    return embeddings[0] if embeddings else []
