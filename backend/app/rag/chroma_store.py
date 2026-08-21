import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class KnowledgeBase:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="reference_knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
        words = text.split()
        chunks = []
        step = max(chunk_size - overlap, 1)
        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks or [text]

    def ingest(self, text: str, source_name: str = "uploaded_document") -> tuple[str, int]:
        document_id = str(uuid.uuid4())
        chunks = self._chunk_text(text)
        ids = [f"{document_id}-{i}" for i in range(len(chunks))]
        metadatas = [{"document_id": document_id, "source": source_name, "chunk_index": i} for i in range(len(chunks))]
        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        return document_id, len(chunks)

    def query(self, query_text: str, document_id: str | None = None, n_results: int = 5) -> list[str]:
        where = {"document_id": document_id} if document_id else None
        results = self.collection.query(query_texts=[query_text], n_results=n_results, where=where)
        docs = results.get("documents", [[]])
        return docs[0] if docs else []


knowledge_base = KnowledgeBase()
