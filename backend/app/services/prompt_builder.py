from pathlib import Path
from typing import Dict, List, Optional


SYSTEM_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "hakuryu_system.md"


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def build_context(sources: List[Dict]) -> str:
    if not sources:
        return "参照できる展示資料は見つかりませんでした。"

    blocks = []
    for index, source in enumerate(sources, start=1):
        metadata = source.get("metadata") or {}
        title = metadata.get("exhibition_name") or metadata.get("source") or f"資料{index}"
        blocks.append(f"[資料{index}: {title}]\n{source.get('content', '')}")
    return "\n\n".join(blocks)


def build_messages(
    user_message: str,
    history: List[Dict[str, str]],
    sources: List[Dict],
    live_context: Optional[str] = None,
) -> List[Dict[str, str]]:
    system_prompt = load_system_prompt()
    context = build_context(sources)
    live_context_block = live_context or "現在のシステム情報は取得できませんでした。"

    messages = [
        {
            "role": "system",
            "content": (
                f"{system_prompt}\n\n"
                "以下の情報だけを根拠に回答してください。資料や現在情報にない内容は推測せず、"
                "「資料では確認できません」と伝えてください。\n"
                "待ち時間、空いている企画、回り方、場所案内は、必ず「現在のシステム情報」を優先してください。\n"
                "展示案内では、必要に応じて「概要」「場所」「所要時間」「注意事項」の順で簡潔に答えてください。\n\n"
                "## 現在のシステム情報\n"
                f"{live_context_block}\n\n"
                "## 参照資料\n"
                f"{context}"
            ),
        }
    ]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": user_message})
    return messages
