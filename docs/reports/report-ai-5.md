# 実装レポート 5：テスト・最適化の基礎実装 (report-ai-5.md)

## 1. 現在の状況
「白龍 AIガイドシステム」の軽量テストと検証導線を整備しました。バックエンドAPI、行程ロジック、フロントエンド型チェックを短時間で確認できる状態になっています。

- **バックエンドAPIテスト**: ヘルスチェック、スタッフ認証、展示、待ち時間、経路、行程APIの基本確認を追加しました。
- **ロジックテスト**: 校内マップの最寄りノード判定と最短経路計算の確認を追加しました。
- **RAG検証スクリプト**: OllamaとChromaDBが準備できた後に検索確認できるスクリプトを追加しました。
- **検証メモ**: 軽量テストとRAG検証を分けて実行する手順を `docs/testing.md` にまとめました。
- **依存関係**: `pytest` をバックエンド依存関係に追加しました。

## 2. 追加・変更した主なファイル
- `docs/tasks/task-ai-5.md`
- `backend/tests/conftest.py`
- `backend/tests/test_api.py`
- `backend/tests/test_logic.py`
- `backend/scripts/check_rag_queries.py`
- `docs/testing.md`
- `backend/requirements.txt`

## 3. 実行した確認
今回は重いAI/Ollama確認は避け、短時間で終わる確認だけ実行しました。

```bash
backend\venv\Scripts\python.exe -m pytest backend\tests -q
```

結果:

- 6件成功
- 1件 warning
- 実行時間 約0.28秒

```bash
frontend\node_modules\.bin\tsc.cmd --noEmit
```

結果:

- 成功

## 4. 確認できたこと
- バックエンドが正常に読み込める
- `GET /health` が成功する
- スタッフPIN認証が成功・失敗を正しく返す
- 展示を作成し、一覧取得できる
- 待ち時間を更新し、一覧取得できる
- 展示間の移動時間を計算できる
- 簡易行程を作成できる
- フロントエンドのTypeScript型チェックが通る

## 5. 人間が知っておくべきこと
普段の開発では、まず軽量テストだけ実行すれば十分です。

```bash
backend\venv\Scripts\python.exe -m pytest backend\tests -q
```

AIやRAGの確認は、Ollama、Embeddingモデル、ChromaDB投入が必要なので別扱いにしています。

```bash
ollama pull nomic-embed-text
ollama run llama3
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py
backend\venv\Scripts\python.exe backend\scripts\check_rag_queries.py
```

## 6. 現段階の注意点
- RAG検索精度の自動採点はまだありません。
- フロントエンドの実ブラウザ操作テストはまだありません。
- SQLAlchemyの `declarative_base()` に関する非推奨warningが1件出ていますが、現時点では動作に影響しません。
- Ollamaを使ったAI回答の本格検証は未実行です。

## 7. 次にすべきこと
- 実データが増えてきたら、RAG検索の質問セットを増やす。
- フロントエンドの主要操作を確認するテストを追加する。
- SQLAlchemyのwarningを解消する。
- AI回答の品質チェック項目を作る。

