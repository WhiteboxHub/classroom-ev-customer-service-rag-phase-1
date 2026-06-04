"""
purge_stale_vectors.py
Removes stale/orphaned vectors from Milvus vector store.
Used after: document deletion, firmware version deprecation, document versioning.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import get_logger
from app.vectorstore.milvus_client import MilvusVectorStore

logger = get_logger(__name__)


def purge_stale_vectors(document_ids: list = None, dry_run: bool = True) -> dict:
    """
    Purge stale vectors from Milvus.
    
    Args:
        document_ids: Specific document IDs to purge. Required for safety.
        dry_run: Default True. Must explicitly disable for actual deletion.
    """
    if not document_ids:
        print("ERROR: document_ids is required. Use --document-ids to specify which documents to purge.")
        print("Use --list to see all indexed documents.")
        return {"status": "error", "reason": "no_document_ids"}
    
    vector_store = MilvusVectorStore()
    vector_store.connect()
    
    if dry_run:
        print(f"DRY RUN: Would purge vectors for {len(document_ids)} documents: {document_ids}")
        return {"status": "dry_run", "would_purge": len(document_ids)}
    
    print(f"Purging vectors for {len(document_ids)} documents...")
    deleted = 0
    errors = 0
    
    for doc_id in document_ids:
        try:
            print(f"  Purging: {doc_id}")
            vector_store.delete_by_document_id(doc_id)
            deleted += 1
            print(f"  OK: Vectors deleted for {doc_id}")
        except Exception as exc:
            print(f"  ERROR: {doc_id}: {exc}")
            errors += 1
    
    result = {"deleted": deleted, "errors": errors, "requested": len(document_ids)}
    print(f"\nPurge complete: {deleted} deleted, {errors} errors")
    logger.info("purge_complete", **result)
    return result


def list_documents():
    """List all indexed documents."""
    vector_store = MilvusVectorStore()
    vector_store.connect()
    docs = vector_store.list_documents()
    print(f"\nIndexed Documents ({len(docs)} total):")
    print("-" * 80)
    for doc in docs:
        print(f"  ID: {doc['document_id']:<30} File: {doc.get('source_file',''):<40} Chunks: {doc.get('chunk_count', '?')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge stale EV RAG vectors")
    parser.add_argument("--document-ids", nargs="+", help="Document IDs to purge")
    parser.add_argument("--list", action="store_true", help="List all indexed documents")
    parser.add_argument("--confirm", action="store_true", help="Disable dry-run and actually purge")
    args = parser.parse_args()
    
    if args.list:
        list_documents()
    else:
        result = purge_stale_vectors(args.document_ids, dry_run=not args.confirm)
        if not args.confirm:
            print("\nThis was a DRY RUN. Use --confirm to actually purge.")
