import json

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    RagIngestResponse,
    RagStatusResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.ollama_client import ollama_client
from app.services.rag_service import rag_service
from app.services.vector_store import VectorStoreUnavailable, vector_store

router = APIRouter(prefix="/api/v1", tags=["AI"])


@router.post("/rag/ingest", response_model=RagIngestResponse)
async def ingest_documents():
    try:
        return await rag_service.ingest()
    except VectorStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/rag/rebuild", response_model=RagIngestResponse)
async def rebuild_documents():
    try:
        return await rag_service.rebuild()
    except VectorStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/rag/status", response_model=RagStatusResponse)
async def rag_status():
    try:
        return rag_service.status()
    except VectorStoreUnavailable as exc:
        status = rag_service.status()
        status["collection_count"] = 0
        status["warning"] = str(exc)
        return status


@router.post("/rag/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    try:
        results = await rag_service.search(request.query, request.top_k, request.filters)
        return {"results": results}
    except VectorStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        history = [message.model_dump() for message in request.history]
        return await rag_service.answer(request.message, history, request.filters)
    except VectorStoreUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = "Ollama API error. Check the model name and Ollama version."
        if exc.response.status_code == 404:
            detail = (
                "Ollama returned 404. The configured model may not exist, or this Ollama "
                "version may not support the requested endpoint."
            )
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama connection error: {exc}") from exc


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_stream():
        try:
            history = [message.model_dump() for message in request.history]
            sources = await rag_service.search(request.message, filters=request.filters)
            yield f"data: {json.dumps({'sources': sources}, ensure_ascii=False)}\n\n"
            messages = rag_service.build_answer_messages(request.message, history, sources)
            stream = await ollama_client.chat(messages, stream=True)
            async for chunk in stream:
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
