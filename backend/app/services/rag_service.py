from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime
from app.services.document_loader import load_documents, summarize_document_sources
from app.services.ollama_client import ollama_client
from app.services.prompt_builder import build_messages
from app.services.vector_store import vector_store


def _wait_label(minutes: int) -> str:
    if minutes <= 5:
        return "空いています"
    if minutes <= 15:
        return "少し待ちます"
    if minutes <= 30:
        return "混雑しています"
    return "かなり混雑しています"


class RagService:
    def status(self) -> Dict[str, Any]:
        summary = summarize_document_sources()
        try:
            summary["collection_count"] = vector_store.count()
        except Exception as exc:
            summary["collection_count"] = 0
            summary["warning"] = str(exc)
        return summary

    async def ingest(self) -> Dict[str, int]:
        documents = load_documents()
        inserted = await vector_store.upsert_documents(documents)
        return {"loaded": len(documents), "upserted": inserted}

    async def rebuild(self) -> Dict[str, int]:
        vector_store.reset_collection()
        return await self.ingest()

    async def search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return await vector_store.search(query, top_k or settings.RAG_TOP_K, filters)

    async def answer(
        self,
        message: str,
        history: List[Dict[str, str]],
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        sources = await self.search(message, filters=filters)
        messages = self.build_answer_messages(message, history, sources)
        response = await ollama_client.chat(messages, stream=False)
        answer = response.get("message", {}).get("content", "")
        return {"answer": answer, "sources": sources, "used_context": bool(sources)}

    def build_answer_messages(
        self,
        message: str,
        history: List[Dict[str, str]],
        sources: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        live_context = self.build_live_context(message)
        return build_messages(message, history, sources, live_context)

    def build_live_context(self, message: str) -> str:
        db = SessionLocal()
        try:
            rows = (
                db.query(Exhibition, WaitTime)
                .outerjoin(WaitTime, WaitTime.exhibition_id == Exhibition.id)
                .order_by(Exhibition.id)
                .all()
            )
        finally:
            db.close()

        if not rows:
            return "現在登録されている企画情報はありません。"

        items = []
        for exhibition, wait_time in rows:
            wait_minutes = wait_time.current_wait_minutes if wait_time else 0
            items.append(
                {
                    "id": exhibition.id,
                    "name": exhibition.name,
                    "category": exhibition.category or "未分類",
                    "location": exhibition.location_name or "場所未設定",
                    "x": exhibition.location_x,
                    "y": exhibition.location_y,
                    "duration": exhibition.duration_minutes or 15,
                    "recommended_for": exhibition.recommended_for or "指定なし",
                    "cautions": exhibition.cautions or "特になし",
                    "stage_start_time": exhibition.stage_start_time or "指定なし",
                    "ticket_status": exhibition.ticket_status or "特になし",
                    "capacity_status": exhibition.capacity_status or "通常",
                    "wait": wait_minutes,
                    "wait_status": _wait_label(wait_minutes),
                }
            )

        quiet = sorted(items, key=lambda item: (item["wait"], item["id"]))[:8]
        crowded = [
            item
            for item in sorted(items, key=lambda item: item["wait"], reverse=True)
            if item["wait"] >= 20
        ][:5]
        route_candidates = self._pick_route_candidates(items)

        all_lines = [
            (
                f"- ID {item['id']} / {item['name']} / {item['category']} / 場所: {item['location']} "
                f"/ 待ち時間: {item['wait']}分 ({item['wait_status']}) / 所要時間: {item['duration']}分 "
                f"/ おすすめ対象: {item['recommended_for']} / 注意事項: {item['cautions']} "
                f"/ 開始時刻: {item['stage_start_time']} / 整理券: {item['ticket_status']} "
                f"/ 定員: {item['capacity_status']} "
                f"/ 座標: ({item['x']}, {item['y']})"
            )
            for item in items
        ]
        quiet_lines = [
            f"- {item['name']} ({item['location']}) 待ち時間{item['wait']}分、所要時間{item['duration']}分"
            for item in quiet
        ]
        crowded_lines = [
            f"- {item['name']} ({item['location']}) 待ち時間{item['wait']}分"
            for item in crowded
        ] or ["- 待ち時間20分以上の企画は現在ありません。"]
        route_lines = [
            f"{index}. {item['name']} ({item['location']}) 待ち時間{item['wait']}分、{item['category']}"
            for index, item in enumerate(route_candidates, start=1)
        ]

        return "\n".join(
            [
                "### 最新待ち時間つき企画一覧",
                *all_lines,
                "",
                "### 今空いている候補",
                *quiet_lines,
                "",
                "### 現在混雑している候補",
                *crowded_lines,
                "",
                "### おすすめ回り方の候補",
                *route_lines,
                "",
                "### 場所案内の使い方",
                "場所を聞かれたら、企画名、場所名、近い企画候補を優先して案内してください。",
                "具体的な校内ルートが資料にない場合は、スタッフ確認を促してください。",
                f"利用者の質問: {message}",
            ]
        )

    def _pick_route_candidates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        selected = []
        used_categories = set()
        for item in sorted(items, key=lambda entry: (entry["wait"], entry["duration"], entry["id"])):
            if item["category"] in used_categories and len(selected) < 3:
                continue
            selected.append(item)
            used_categories.add(item["category"])
            if len(selected) >= 4:
                break
        return selected or sorted(items, key=lambda entry: (entry["wait"], entry["id"]))[:4]

    async def answer_stream(
        self,
        message: str,
        history: List[Dict[str, str]],
        filters: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        sources = await self.search(message, filters=filters)
        messages = self.build_answer_messages(message, history, sources)
        stream = await ollama_client.chat(messages, stream=True)
        async for chunk in stream:
            yield chunk


rag_service = RagService()
