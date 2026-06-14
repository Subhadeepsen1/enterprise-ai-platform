"""
Enterprise RAG (Retrieval Augmented Generation) Pipeline.
Uses ChromaDB for vector storage and sentence-transformers for embeddings.
"""

import logging
import hashlib
from typing import Optional
import os

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Production RAG pipeline using ChromaDB + sentence-transformers.
    Falls back to keyword search if vector search is unavailable.
    """

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K = 5

    def __init__(self):
        self._client = None
        self._collection = None
        self._embedder = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of heavy ML components."""
        if self._initialized:
            return
        
        from app.core.config import settings
        
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
            self._client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name="enterprise_documents",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Using in-memory fallback.")
            self._collection = None

        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model loaded: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Embedding model failed to load: {e}")
            self._embedder = None
        
        self._initialized = True

    def chunk_text(self, text: str) -> list[dict]:
        """Split text into overlapping chunks for indexing."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.CHUNK_SIZE - self.CHUNK_OVERLAP):
            chunk_words = words[i: i + self.CHUNK_SIZE]
            if len(chunk_words) < 10:
                break
            chunk_text = " ".join(chunk_words)
            chunks.append({
                "text": chunk_text,
                "start_word": i,
                "end_word": i + len(chunk_words),
                "chunk_index": len(chunks),
            })
        
        return chunks

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        self._initialize()
        
        if self._embedder is None:
            # Fallback: return simple hash-based pseudo-embeddings
            return [[hash(t) % 1000 / 1000.0] * 384 for t in texts]
        
        return self._embedder.encode(texts, normalize_embeddings=True).tolist()

    def index_document(self, document_id: int, text: str, metadata: dict) -> str:
        """
        Index a document into the vector store.
        Returns a vector store collection ID.
        """
        self._initialize()
        
        chunks = self.chunk_text(text)
        if not chunks:
            logger.warning(f"No chunks generated for document {document_id}")
            return f"doc_{document_id}"
        
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embed_texts(chunk_texts)
        
        ids = [f"doc_{document_id}_chunk_{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "document_id": str(document_id),
                "chunk_index": str(c["chunk_index"]),
                "filename": metadata.get("filename", ""),
                "doc_type": metadata.get("doc_type", ""),
                **{k: str(v) for k, v in metadata.items()},
            }
            for c in chunks
        ]
        
        if self._collection is not None:
            try:
                # Remove existing chunks for this document
                existing = self._collection.get(
                    where={"document_id": str(document_id)}
                )
                if existing["ids"]:
                    self._collection.delete(ids=existing["ids"])
                
                self._collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunk_texts,
                    metadatas=metadatas,
                )
                logger.info(f"Indexed {len(chunks)} chunks for document {document_id}")
            except Exception as e:
                logger.error(f"Failed to index document {document_id}: {e}")
        
        return f"doc_{document_id}"

    def retrieve_context(self, query: str, top_k: int = None, document_ids: list[int] = None) -> list[dict]:
        """
        Retrieve the most relevant chunks for a query.
        Returns list of dicts with text, source, and score.
        """
        self._initialize()
        k = top_k or self.TOP_K
        
        if self._collection is None or self._embedder is None:
            return self._keyword_fallback(query, k)
        
        try:
            query_embedding = self.embed_texts([query])[0]
            
            where_clause = None
            if document_ids:
                where_clause = {"document_id": {"$in": [str(d) for d in document_ids]}}
            
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, self._collection.count() or 1),
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )
            
            contexts = []
            for i, (doc, meta, dist) in enumerate(
                zip(results["documents"][0], results["metadatas"][0], results["distances"][0])
            ):
                contexts.append({
                    "text": doc,
                    "source": meta.get("filename", "Unknown Document"),
                    "document_id": int(meta.get("document_id", 0)),
                    "doc_type": meta.get("doc_type", ""),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "relevance_score": round(1 - dist, 3),
                })
            
            return contexts
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            return self._keyword_fallback(query, k)

    def _keyword_fallback(self, query: str, k: int) -> list[dict]:
        """Simple keyword-based fallback when vector search is unavailable."""
        return [{
            "text": f"[Vector search unavailable] Related to: {query}",
            "source": "System",
            "document_id": 0,
            "doc_type": "unknown",
            "chunk_index": 0,
            "relevance_score": 0.5,
        }]

    def generate_answer(self, query: str, contexts: list[dict], conversation_history: list[dict] = None) -> dict:
        """
        Generate an answer using retrieved context.
        Uses OpenAI if available, otherwise returns context-based response.
        """
        from app.core.config import settings
        
        context_text = "\n\n---\n\n".join([
            f"[Source: {c['source']}]\n{c['text']}"
            for c in contexts[:self.TOP_K]
        ])
        
        system_prompt = """You are an Enterprise AI Assistant for a consulting firm. 
        Answer questions ONLY based on the provided document context. 
        If the context doesn't contain the answer, clearly state that.
        Always cite your sources. Be precise, professional, and concise.
        Format monetary values and dates clearly."""

        user_message = f"""Context from company documents:

{context_text}

---

Question: {query}

Please provide a precise answer based on the context above. Cite specific sources."""

        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            messages = [{"role": "system", "content": system_prompt}]
            
            if conversation_history:
                for msg in conversation_history[-6:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": user_message})
            
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=1024,
            )
            
            answer = response.choices[0].message.content
            
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}. Using context-based response.")
            # Intelligent fallback: summarize context
            if contexts:
                answer = f"Based on the available documents:\n\n"
                for ctx in contexts[:3]:
                    answer += f"**From {ctx['source']}:**\n{ctx['text'][:300]}...\n\n"
                answer += f"\n*Note: AI generation is unavailable. Showing raw document excerpts.*"
            else:
                answer = "No relevant information found in the indexed documents for your query."
        
        sources = [
            {
                "filename": c["source"],
                "document_id": c["document_id"],
                "relevance": c["relevance_score"],
                "chunk": c["chunk_index"],
            }
            for c in contexts[:self.TOP_K]
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "context_used": len(contexts),
        }


# Singleton instance
rag_pipeline = RAGPipeline()
