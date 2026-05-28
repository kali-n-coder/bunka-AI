from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)
    user_type: str = "visitor"
    filters: Optional[Dict[str, Any]] = None
    stream: bool = False


class SourceChunk(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    distance: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk] = Field(default_factory=list)
    used_context: bool = False


class SearchRequest(BaseModel):
    query: str
    top_k: int = 4
    filters: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    results: List[SourceChunk]


class RagSourceFile(BaseModel):
    path: str
    type: str
    chunk_count: int


class RagStatusResponse(BaseModel):
    data_dir: str
    file_count: int
    chunk_count: int
    collection_count: int
    sources: List[RagSourceFile] = Field(default_factory=list)
    warning: Optional[str] = None


class RagIngestResponse(BaseModel):
    loaded: int
    upserted: int
