"""
backfill_embeddings.py
Operational script to backfill missing embeddings for documents in Milvus.
Used when: embedding model is upgraded, vectors are corrupted, new documents lack embeddings.
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.vectorstore.milvus_client import MilvusVectorStore

logger = get_logger(__name__)


def backfill_embeddings(document_ids: list = None, dry_run: bool = False) -> dict:
    """
    Backfill embeddings for specified documents or all documents missing vectors.
    
    Args:
        document_ids: List of document IDs to backfill. If None, processes all.
        dry_run: If True, only counts without updating.
    """
    vector_store = MilvusVectorStore()
    embedding_service = EmbeddingService()
    
    print("Connecting to Milvus...")
    vector_store.connect()
    
    # List all documents
    all_docs = vector_store.list_documents()
    
    if document_ids:
        target_docs = [d for d in all_docs if d["document_id"] in document_ids]
    else:
        target_docs = all_docs
    
    print(f"Found {len(target_docs)} documents to process")
    
    if dry_run:
        print(f"DRY RUN: Would backfill embeddings for {len(target_docs)} documents")
        return {"total": len(target_docs), "processed": 0, "dry_run": True}
    
    processed = 0
    errors = 0
    
    for doc in target_docs:
        doc_id = doc["document_id"]
        source_file = doc.get("source_file", "unknown")
        
        try:
            print(f"Processing: {source_file} ({doc_id})")
            chunks = vector_store.get_chunks_by_document_id(doc_id)
            
            if not chunks:
                print(f"  SKIP: No chunks found for {doc_id}")
                continue
            
            texts = [c["text"] for c in chunks]
            new_embeddings = embedding_service.embed_documents(texts)
            vector_store.update_embeddings(doc_id, new_embeddings)
            print(f"  OK: Re-embedded {len(chunks)} chunks")
            processed += 1
        except Exception as exc:
            print(f"  ERROR: {doc_id}: {exc}")
            errors += 1
    
    result = {"total": len(target_docs), "processed": processed, "errors": errors}
    print(f"\nBackfill complete: {processed} processed, {errors} errors")
    logger.info("backfill_complete", **result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill EV RAG embeddings")
    parser.add_argument("--document-ids", nargs="+", help="Specific document IDs to backfill")
    parser.add_argument("--dry-run", action="store_true", help="Count only, no changes")
    args = parser.parse_args()
    
    result = backfill_embeddings(args.document_ids, args.dry_run)
    sys.exit(0 if result["errors"] == 0 else 1)
