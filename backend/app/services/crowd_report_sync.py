import asyncio
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

STATUSES = ("empty", "short", "busy", "closed")
STATUS_ORDER = {status: index for index, status in enumerate(STATUSES)}
STATUS_LABELS = {
    "empty": "すぐ入れそう",
    "short": "少し待つかも",
    "busy": "かなり混んでいる",
    "closed": "受付停止・満員っぽい",
}


class CrowdReportSyncService:
    def __init__(self):
        self._summary: list[dict[str, Any]] = []
        self._last_synced_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.FIREBASE_CROWD_REPORTS_URL.strip())

    def _url(self) -> str:
        raw_url = settings.FIREBASE_CROWD_REPORTS_URL.strip()
        if not raw_url:
            return ""

        url = raw_url if raw_url.endswith(".json") else f"{raw_url.rstrip('/')}.json"
        if settings.FIREBASE_CROWD_REPORTS_AUTH:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode({'auth': settings.FIREBASE_CROWD_REPORTS_AUTH})}"
        return url

    def _created_at_to_datetime(self, value: Any) -> datetime | None:
        try:
            timestamp = float(value)
        except (TypeError, ValueError):
            return None
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    def _iter_reports(self, payload: Any):
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    yield item
            return
        if not isinstance(payload, dict):
            return

        for raw_exhibition_id, reports in payload.items():
            if isinstance(reports, dict) and {"status", "createdAt"}.issubset(reports.keys()):
                report = dict(reports)
                report.setdefault("exhibitionId", raw_exhibition_id)
                yield report
                continue
            if not isinstance(reports, dict):
                continue
            for item in reports.values():
                if not isinstance(item, dict):
                    continue
                report = dict(item)
                report.setdefault("exhibitionId", raw_exhibition_id)
                yield report

    def _normalize_report(self, report: dict[str, Any]) -> tuple[int, str, datetime] | None:
        try:
            exhibition_id = int(report.get("exhibitionId"))
        except (TypeError, ValueError):
            return None

        status = str(report.get("status", ""))
        if status not in STATUS_ORDER:
            return None

        created_at = self._created_at_to_datetime(report.get("createdAt"))
        if created_at is None:
            return None
        return exhibition_id, status, created_at

    def _summarize(self, payload: Any) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        window_minutes = max(settings.CROWD_REPORT_WINDOW_MINUTES, 1)
        window_start = now - timedelta(minutes=window_minutes)
        grouped: dict[int, list[tuple[str, datetime]]] = defaultdict(list)

        for raw_report in self._iter_reports(payload) or []:
            normalized = self._normalize_report(raw_report)
            if normalized is None:
                continue
            exhibition_id, status, created_at = normalized
            if created_at >= window_start:
                grouped[exhibition_id].append((status, created_at))

        summary = []
        for exhibition_id in sorted(grouped):
            reports = grouped[exhibition_id]
            counts = Counter(status for status, _created_at in reports)
            status = max(counts, key=lambda item: (counts[item], STATUS_ORDER[item]))
            last_reported_at = max(created_at for _status, created_at in reports)
            summary.append(
                {
                    "exhibition_id": exhibition_id,
                    "status": status,
                    "label": STATUS_LABELS[status],
                    "report_count": len(reports),
                    "last_reported_at": last_reported_at,
                    "source": "visitor",
                }
            )
        return summary

    async def sync(self) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "synced": False,
                "report_count": 0,
                "summary_count": len(self._summary),
                "last_synced_at": self._last_synced_at,
                "error": None,
            }

        async with self._lock:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(self._url())
                    response.raise_for_status()
                summary = self._summarize(response.json())
                self._summary = summary
                self._last_synced_at = datetime.now(timezone.utc)
                self._last_error = None
                return {
                    "enabled": True,
                    "synced": True,
                    "report_count": sum(item["report_count"] for item in summary),
                    "summary_count": len(summary),
                    "last_synced_at": self._last_synced_at,
                    "error": None,
                }
            except Exception as exc:
                self._last_error = str(exc)
                logger.warning("Failed to sync visitor crowd reports: %s", exc)
                return {
                    "enabled": True,
                    "synced": False,
                    "report_count": sum(item["report_count"] for item in self._summary),
                    "summary_count": len(self._summary),
                    "last_synced_at": self._last_synced_at,
                    "error": self._last_error,
                }

    async def summary(self) -> list[dict[str, Any]]:
        if self.enabled and self._last_synced_at is None:
            await self.sync()
        return list(self._summary)

    async def _loop(self):
        while True:
            await self.sync()
            await asyncio.sleep(max(settings.FIREBASE_CROWD_SYNC_INTERVAL_SECONDS, 10))

    def start_background_sync(self):
        if not self.enabled or self._task:
            return
        self._task = asyncio.create_task(self._loop())


crowd_report_sync_service = CrowdReportSyncService()
