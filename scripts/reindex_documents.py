"""
reindex_documents.py
Re-indexes all EV documents after chunking strategy changes or schema updates.
Preserves document metadata while regenerating vectors with updated settings.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import get_logger
from app.ingestion.pipeline import IngestionPipeline

logger = get_logger(__name__)


DATA_DIRECTORIES = [
    "data/battery_manuals",
    "data/charging_docs",
    "data/firmware_updates",
    "data/dtc_codes",
    "data/service_manuals",
    "data/technician_notes",
    "data/ota_release_notes",
    "data/sample_ev_docs",
]


def reindex_all(dry_run: bool = False) -> dict:
    """
    Re-ingest all EV domain data directories.
    Use after: chunking strategy changes, schema updates, embedding model changes.
    """
    print("EV RAG Reindexing Operation")
    print("=" * 60)
    
    if dry_run:
        print("DRY RUN: Scanning directories only, no ingestion")
        for d in DATA_DIRECTORIES:
            path = Path(d)
            if path.exists():
                files = list(path.rglob("*.md")) + list(path.rglob("*.pdf")) + list(path.rglob("*.txt"))
                print(f"  {d}: {len(files)} files found")
            else:
                print(f"  {d}: DIRECTORY NOT FOUND")
        return {"status": "dry_run"}
    
    pipeline = IngestionPipeline()
    total_results = []
    
    for directory in DATA_DIRECTORIES:
        path = Path(directory)
        if not path.exists():
            print(f"SKIP: {directory} (not found)")
            continue
        
        print(f"\nIngesting: {directory}")
        try:
            results = pipeline.ingest_directory(path)
            total_results.extend(results)
            total_chunks = sum(r.get("chunks_indexed", 0) for r in results)
            print(f"  OK: {len(results)} documents, {total_chunks} chunks")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            logger.error("reindex_directory_failed", directory=directory, error=str(exc))
    
    total_chunks = sum(r.get("chunks_indexed", 0) for r in total_results)
    result = {"documents": len(total_results), "total_chunks": total_chunks}
    print(f"\nReindex complete: {len(total_results)} documents, {total_chunks} chunks")
    logger.info("reindex_complete", **result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reindex all EV RAG documents")
    parser.add_argument("--dry-run", action="store_true", help="Scan only, do not ingest")
    args = parser.parse_args()
    
    result = reindex_all(args.dry_run)
    sys.exit(0)
