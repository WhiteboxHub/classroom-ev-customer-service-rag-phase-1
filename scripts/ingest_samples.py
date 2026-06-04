"""CLI script to ingest the sample EV troubleshooting dataset."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.logging import configure_logging, get_logger
from app.ingestion.pipeline import IngestionPipeline

configure_logging()
logger = get_logger(__name__)


def main() -> None:
    pipeline = IngestionPipeline()
    sample_dir = ROOT / "data" / "sample_ev_docs"
    results = pipeline.ingest_directory(sample_dir)
    total = sum(r["chunks_indexed"] for r in results)
    logger.info("sample_ingestion_complete", files=len(results), chunks=total)
    print(f"Ingested {len(results)} files, {total} chunks indexed.")


if __name__ == "__main__":
    main()
