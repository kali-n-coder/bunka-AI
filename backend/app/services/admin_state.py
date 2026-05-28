import logging
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List


class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity: int = 120):
        super().__init__()
        self.records: Deque[Dict[str, Any]] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(
            {
                "time": datetime.fromtimestamp(record.created).isoformat(timespec="seconds"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        )

    def recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.records)[-limit:]


memory_log_handler = MemoryLogHandler()


def install_memory_logging() -> None:
    root = logging.getLogger()
    if memory_log_handler not in root.handlers:
        root.addHandler(memory_log_handler)
