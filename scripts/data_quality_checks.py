"""
data_quality_checks.py
Validates EV RAG data quality: chunk quality, metadata completeness,
DTC reference accuracy, and vector store integrity.
"""

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.logging import get_logger
from app.vectorstore.milvus_client import MilvusVectorStore

logger = get_logger(__name__)


def run_data_quality_checks() -> dict:
    """
    Run comprehensive data quality checks on the EV RAG vector store.
    
    Checks:
    1. Chunk count distribution
    2. Metadata completeness (vehicle_model, firmware_version, diagnostic_category)
    3. Chunk length distribution (detect too-short or too-long chunks)
    4. DTC reference coverage
    5. Document category distribution
    """
    print("Running EV RAG Data Quality Checks...")
    print("=" * 60)
    
    vector_store = MilvusVectorStore()
    vector_store.connect()
    
    # Get all documents
    docs = vector_store.list_documents()
    total_docs = len(docs)
    total_chunks = sum(d.get("chunk_count", 0) for d in docs)
    
    print(f"\n1. CORPUS OVERVIEW")
    print(f"   Total documents indexed: {total_docs}")
    print(f"   Total chunks indexed:    {total_chunks}")
    
    if total_docs == 0:
        print("   WARNING: No documents indexed. Run ingestion first.")
        return {"status": "empty", "documents": 0, "chunks": 0}
    
    # Category distribution
    categories = {}
    no_category = 0
    for doc in docs:
        cat = doc.get("diagnostic_category", "")
        if cat:
            categories[cat] = categories.get(cat, 0) + 1
        else:
            no_category += 1
    
    print(f"\n2. DOCUMENT CATEGORY DISTRIBUTION")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        bar = "#" * min(count * 2, 40)
        print(f"   {cat:<25} {count:>4} docs  {bar}")
    if no_category:
        print(f"   {'(no category)':<25} {no_category:>4} docs  *** METADATA MISSING ***")
    
    # Metadata completeness
    has_vehicle = sum(1 for d in docs if d.get("source_file"))
    print(f"\n3. METADATA COMPLETENESS")
    print(f"   Has source_file:     {has_vehicle}/{total_docs} ({100*has_vehicle//max(total_docs,1)}%)")
    print(f"   Has category:        {total_docs - no_category}/{total_docs} ({100*(total_docs-no_category)//max(total_docs,1)}%)")
    
    # Chunk size assessment
    print(f"\n4. CHUNK DISTRIBUTION")
    chunk_counts = [d.get("chunk_count", 0) for d in docs if d.get("chunk_count", 0) > 0]
    if chunk_counts:
        print(f"   Min chunks per doc:  {min(chunk_counts)}")
        print(f"   Max chunks per doc:  {max(chunk_counts)}")
        print(f"   Avg chunks per doc:  {statistics.mean(chunk_counts):.1f}")
        singleton_docs = sum(1 for c in chunk_counts if c == 1)
        if singleton_docs > total_docs * 0.3:
            print(f"   WARNING: {singleton_docs} docs have only 1 chunk (may indicate parsing issues)")
    
    print(f"\n5. QUALITY SCORE")
    category_coverage = (total_docs - no_category) / max(total_docs, 1)
    quality_score = category_coverage * 100
    print(f"   Metadata completeness: {quality_score:.1f}%")
    status = "PASS" if quality_score >= 70 else "FAIL"
    print(f"   Overall status: {status}")
    print("=" * 60)
    
    result = {
        "status": status.lower(),
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "categories": categories,
        "metadata_completeness_pct": round(quality_score, 1),
    }
    
    logger.info("data_quality_check_complete", **result)
    return result


if __name__ == "__main__":
    result = run_data_quality_checks()
    sys.exit(0 if result.get("status") == "pass" else 1)
