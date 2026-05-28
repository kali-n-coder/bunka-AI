from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.document_loader import DocumentChunk
from app.services.embedding_client import embedding_client


class VectorStoreUnavailable(RuntimeError):
    pass


class VectorStore:
    def __init__(self):
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreUnavailable(
                "ChromaDB is not installed. Run `pip install -r backend/requirements.txt`."
            ) from exc

        self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._collection = self._client.get_or_create_collection(settings.CHROMA_COLLECTION_NAME)
        return self._collection

    async def upsert_documents(self, documents: List[DocumentChunk]) -> int:
        if not documents:
            return 0

        collection = self._get_collection()
        embeddings = [await embedding_client.embed(document.content) for document in documents]
        collection.upsert(
            ids=[document.id for document in documents],
            documents=[document.content for document in documents],
            metadatas=[document.metadata for document in documents],
            embeddings=embeddings,
        )
        return len(documents)

    async def search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        collection = self._get_collection()
        embedding = await embedding_client.embed(query)
        result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k or settings.RAG_TOP_K,
            where=filters or None,
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            {
                "content": content,
                "metadata": metadata or {},
                "distance": distance,
            }
            for content, metadata, distance in zip(documents, metadatas, distances)
        ]

    def count(self) -> int:
        return self._get_collection().count()

    def reset_collection(self) -> None:
        collection = self._get_collection()
        ids = collection.get().get("ids", [])
        if ids:
            collection.delete(ids=ids)


vector_store = VectorStore()
