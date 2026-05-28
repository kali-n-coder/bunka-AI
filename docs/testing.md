# テスト・検証メモ

このプロジェクトでは、短時間で壊れていないことを確認するテストと、OllamaやRAGを使う重めの検証を分けます。

## 軽量テスト

バックエンドAPIとロジックの基本確認です。Ollamaは不要です。

```bash
cd backend
venv\Scripts\python.exe -m pytest tests
```

## フロントエンド確認

TypeScriptの型確認です。

```bash
cd frontend
npm run build
```

## RAG検索確認

Ollama、Embeddingモデル、ChromaDBへのデータ投入が必要です。

```bash
ollama pull nomic-embed-text
ollama run llama3
cd backend
venv\Scripts\python.exe scripts\ingest_documents.py
venv\Scripts\python.exe scripts\check_rag_queries.py
```

RAG検索確認は環境準備に時間がかかるため、普段の軽量テストとは分けて実行します。

