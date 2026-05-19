"""Ingest policy PDFs into Qdrant.

Usage:
    python -m scripts.ingest_policies path/to/policy_pdfs/

Each PDF in the directory becomes 1+ chunks in the `policy_chunks` collection,
keyed by stable IDs, with payload metadata (policy_id, policy_name, section,
source_file). Re-running is idempotent at the chunk level (Qdrant assigns new
point IDs, so duplicates are possible — clean the collection first if needed).
"""
import sys
from pathlib import Path

from app.services.ai.policy_ingest import ingest_directory


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.ingest_policies <directory>")
        sys.exit(2)

    directory = Path(sys.argv[1])
    if not directory.is_dir():
        print(f"Not a directory: {directory}")
        sys.exit(1)

    results = ingest_directory(directory)
    total = sum(results.values())
    print(f"\nIngestion complete. {total} total chunks across {len(results)} PDFs:")
    for name, count in results.items():
        print(f"  {name:40s} {count} chunks")


if __name__ == "__main__":
    main()
