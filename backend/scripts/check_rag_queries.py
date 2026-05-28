import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.services.rag_service import rag_service


QUERIES = [
    "白龍の舞はどこで見られますか？",
    "龍の巣カフェでは何が楽しめますか？",
    "白龍の舞の注意事項を教えてください。",
]


async def main():
    for query in QUERIES:
        print(f"\nQuery: {query}")
        try:
            results = await rag_service.search(query, top_k=3)
        except Exception as exc:
            print(f"RAG search is not ready: {exc}")
            print("Ollama, embedding model, and ChromaDB ingestion may be required.")
            return

        if not results:
            print("No results. Run the ingestion endpoint or script first.")
            continue

        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            content = result.get("content", "").replace("\n", " ")
            print(f"{index}. source={metadata.get('source', 'unknown')}")
            print(f"   text={content[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
