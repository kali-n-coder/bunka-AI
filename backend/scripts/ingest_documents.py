import argparse
import asyncio
import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

from app.services.document_loader import load_documents
from app.services.vector_store import vector_store


async def main():
    parser = argparse.ArgumentParser(description="RAG用資料をベクトルDBへ投入します。")
    parser.add_argument("--profile", choices=["sample", "production"], default="sample")
    parser.add_argument("--data-dir", help="直接投入する資料フォルダ")
    args = parser.parse_args()

    data_dir = Path(args.data_dir) if args.data_dir else PROJECT_ROOT / "docs" / "data" / args.profile
    documents = [
        document
        for document in load_documents(str(data_dir))
        if Path(str(document.metadata.get("source", ""))).name.lower() != "readme.md"
    ]
    upserted = await vector_store.upsert_documents(documents)
    print(f"Data dir: {data_dir}")
    print(f"Loaded: {len(documents)}")
    print(f"Upserted: {upserted}")


if __name__ == "__main__":
    asyncio.run(main())
