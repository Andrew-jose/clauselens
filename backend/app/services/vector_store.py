import logging
import os
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger(__name__)

_chroma_client = None
_chunks_collection = None


def get_chroma_client():
    """Singleton ChromaDB embedded client."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


def get_chunks_collection():
    """Get or create the cached main chunks vector collection."""
    global _chunks_collection
    if _chunks_collection is None:
        client = get_chroma_client()
        _chunks_collection = client.get_or_create_collection(
            name="clauselens_chunks",
            metadata={"hnsw:space": "cosine"},
        )
    return _chunks_collection


def index_chunks(document_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
    """Index a list of document chunks with their embeddings into ChromaDB."""
    if not chunks:
        return

    collection = get_chunks_collection()

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "page_number": int(chunk.get("page_number", 1)),
            "clause_id": str(chunk.get("clause_id") or ""),
            "section_heading": str(chunk.get("section_heading") or ""),
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def search_chunks(
    query_embedding: List[float],
    document_id: str,
    top_k: int = 10,
    where_filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Retrieve top-k chunks for a document given a query embedding."""
    collection = get_chunks_collection()

    # Always enforce document scoping
    scoped_where = {"document_id": document_id}
    if where_filter:
        scoped_where = {"$and": [scoped_where, where_filter]}

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=scoped_where,
        )
    except Exception as e:
        logger.warning(f"ChromaDB query failed for document {document_id}: {e}")
        return []

    retrieved = []
    if results and "ids" in results and results["ids"]:
        ids = results["ids"][0]
        docs = results["documents"][0] if "documents" in results else []
        metas = results["metadatas"][0] if "metadatas" in results else []
        distances = results["distances"][0] if "distances" in results else []

        for i in range(len(ids)):
            retrieved.append({
                "id": ids[i],
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
                "distance": distances[i] if i < len(distances) else 1.0,
            })

    return retrieved


def delete_document_vectors(document_id: str):
    """Delete all indexed vectors for a document."""
    try:
        collection = get_chunks_collection()
        collection.delete(where={"document_id": document_id})
    except Exception as e:
        logger.warning(f"Failed to delete ChromaDB vectors for document {document_id}: {e}")

