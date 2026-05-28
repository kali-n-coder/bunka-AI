# 実装レポート 2：RAG & AIロジックの基礎実装 (report-ai-2.md)

## 1. 現在の状況
「白龍 AIガイドシステム」の RAG & AIロジックの基礎部分を実装しました。具体的には、展示資料を読み込み、ベクトルDBへ投入し、ユーザーの質問に関連する資料を検索して、Ollama に渡すための流れを準備しています。

- **RAG用データ**: `docs/data/` にサンプル展示データを追加しました。
- **ドキュメント読み込み**: Markdown / JSON 形式の資料を読み込む仕組みを追加しました。
- **Embedding接続**: Ollama の Embedding API を呼び出すクライアントを追加しました。
- **ベクトルDB**: ChromaDB を使うためのベクトルストアを追加しました。
- **RAGサービス**: 検索、プロンプト生成、Ollama への問い合わせをまとめるサービスを追加しました。
- **チャットAPI**: 通常回答とストリーミング回答のAPIを追加しました。
- **フロント連携**: フロントエンド側のAPIクライアントにチャット・ストリーミング・RAG状態確認の関数を追加しました。

## 2. 現在の状況でできること
以下のAPIが追加されました。

- `GET /api/v1/rag/status`: RAG用ベクトルDBの登録件数を確認できます。
- `POST /api/v1/rag/ingest`: `docs/data/` の資料をベクトルDBへ投入します。
- `POST /api/v1/rag/search`: 質問に近い資料チャンクを検索します。
- `POST /api/v1/chat`: RAG検索結果を使ってAI回答を生成します。
- `POST /api/v1/chat/stream`: AI回答をストリーミング形式で返します。

## 3. 追加・変更した主なファイル
- `backend/app/api/chat.py`
- `backend/app/schemas/chat.py`
- `backend/app/services/document_loader.py`
- `backend/app/services/embedding_client.py`
- `backend/app/services/vector_store.py`
- `backend/app/services/prompt_builder.py`
- `backend/app/services/rag_service.py`
- `backend/app/prompts/hakuryu_system.md`
- `backend/scripts/ingest_documents.py`
- `docs/data/sample_exhibitions.md`
- `frontend/src/api/client.ts`
- `backend/requirements.txt`
- `backend/app/core/config.py`
- `backend/app/main.py`

## 4. 検証結果
- バックエンドの import 確認: 成功
- RAG用サンプルデータ読み込み: 成功（10チャンク）
- FastAPI ルート追加確認: 成功
- ChromaDB 初期化確認: 成功（現在の登録件数 0）
- `GET /health`: 成功
- `GET /api/v1/rag/status`: 成功
- フロントエンド TypeScript チェック: 成功

## 5. 人間が知っておくべきこと
- `chromadb` は `backend/requirements.txt` に追加済みで、現在の `backend/venv` にもインストールされています。
- 実際に `POST /api/v1/rag/ingest` を成功させるには、Ollama が起動していて、Embeddingモデルが使える必要があります。
- 現在の設定では Embeddingモデルは `nomic-embed-text` です。
- 必要に応じて、以下を事前に実行してください。

```bash
ollama pull nomic-embed-text
ollama run llama3
```

## 6. 次にすべきこと
- Ollama を起動した状態で `POST /api/v1/rag/ingest` を実行し、サンプル展示データを ChromaDB に投入する。
- `POST /api/v1/rag/search` で「白龍の舞はどこ？」などの質問を試す。
- `POST /api/v1/chat` で、RAG検索結果を使った回答生成を確認する。
- フロントエンドに実際のチャット画面を作成する。

