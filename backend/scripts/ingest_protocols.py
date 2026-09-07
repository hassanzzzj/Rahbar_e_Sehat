"""CLI script to ingest clinical protocol documents into the FAISS vector store."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.logging import get_logger, setup_logging
from app.rag.ingestion import ingest_clinical_protocols
from app.rag.vector_store import FAISSVectorStore

logger = get_logger(__name__)

DEFAULT_PROTOCOLS_DIR = PROJECT_ROOT / "data" / "protocols"
DEFAULT_STORE_PATH = PROJECT_ROOT / "data" / "vector_store"


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Ingest clinical protocol documents into the FAISS vector store.",
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=str(DEFAULT_PROTOCOLS_DIR),
        help=f"Directory containing protocol .md/.txt files (default: {DEFAULT_PROTOCOLS_DIR})",
    )
    parser.add_argument(
        "--store-path",
        type=str,
        default=str(DEFAULT_STORE_PATH),
        help=f"Path to persist the FAISS index (default: {DEFAULT_STORE_PATH})",
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=384,
        help="Embedding vector dimension (default: 384 for MiniLM-L12-v2)",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: source directory does not exist: {source_dir}", file=sys.stderr)
        sys.exit(1)

    store_path = Path(args.store_path)
    store_path.mkdir(parents=True, exist_ok=True)

    print(f"Source directory : {source_dir}")
    print(f"Store path       : {store_path}")
    print(f"Vector dimension : {args.dimension}")
    print()

    vector_store = FAISSVectorStore(
        dimension=args.dimension,
        store_path=str(store_path),
    )

    total = ingest_clinical_protocols(
        source_dir=str(source_dir),
        vector_store=vector_store,
    )

    print(f"\nIngestion complete. {total} chunks indexed.")


if __name__ == "__main__":
    main()
