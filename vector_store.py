import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict, Any
import numpy as np

from models import DocumentChunk, RetrievedDocument
from config import settings


class VectorStore:
    """Vector store for document embeddings using ChromaDB"""

    def __init__(self):
        """Initialize vector store and embedding model"""

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="clara_documents",
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.embedding_model)

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the vector store"""

        if not chunks:
            return

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata
            }
            for chunk in chunks
        ]

        # Generate embeddings
        embeddings = self.embedding_model.encode(
            documents,
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()

        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search(
        self,
        query: str,
        top_k: int = None,
        filter_dict: Dict[str, Any] = None
    ) -> List[RetrievedDocument]:
        """Search for relevant document chunks"""

        if top_k is None:
            top_k = settings.top_k_documents

        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            show_progress_bar=False,
            convert_to_numpy=True
        ).tolist()

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict
        )

        # Convert results to RetrievedDocument objects
        retrieved_docs = []

        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                chunk = DocumentChunk(
                    chunk_id=results['ids'][0][i],
                    document_id=results['metadatas'][0][i]['document_id'],
                    content=results['documents'][0][i],
                    chunk_index=results['metadatas'][0][i]['chunk_index'],
                    metadata=results['metadatas'][0][i]
                )

                retrieved_doc = RetrievedDocument(
                    chunk=chunk,
                    relevance_score=1.0 - results['distances'][0][i]  # Convert distance to similarity
                )

                retrieved_docs.append(retrieved_doc)

        return retrieved_docs

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks of a document"""

        # Query all chunks with this document_id
        results = self.collection.get(
            where={"document_id": document_id}
        )

        if results['ids']:
            self.collection.delete(ids=results['ids'])

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all document metadata"""

        results = self.collection.get()

        # Extract unique documents
        documents = {}
        if results['metadatas']:
            for metadata in results['metadatas']:
                doc_id = metadata['document_id']
                if doc_id not in documents:
                    documents[doc_id] = {
                        'document_id': doc_id,
                        'source_file': metadata.get('source_file', 'Unknown'),
                        'chunks': 0
                    }
                documents[doc_id]['chunks'] += 1

        return list(documents.values())

    def clear_all(self) -> None:
        """Clear all documents from the vector store"""
        self.client.delete_collection("clara_documents")
        self.collection = self.client.get_or_create_collection(
            name="clara_documents",
            metadata={"hnsw:space": "cosine"}
        )

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.collection.count()
        documents = self.get_all_documents()

        return {
            "total_chunks": count,
            "total_documents": len(documents),
            "documents": documents
        }
