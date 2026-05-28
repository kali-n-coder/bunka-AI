# サンプルデータで試すための初期設定ガイド

本番データがまだ揃っていない段階でも、サンプルデータで白龍AIガイドを試せます。  
当日確認では [operation_checklist.md](operation_checklist.md) も使ってください。

## 1. サンプルデータ

サンプルデータは以下に分かれています。

- `docs/data/sample/exhibitions.csv`: 企画一覧、場所、所要時間、初期待ち時間
- `docs/data/sample/knowledge.json`: AI/RAG用の企画説明
- `docs/data/sample/knowledge.md`: AI/RAG用の補足資料

本番データを作るときは `docs/data/production/` に同じ名前で置きます。

## 2. 企画データをチェックする

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile sample
```

`OK` と表示されれば大丈夫です。

## 3. 企画データをSQLiteへ投入する

```bash
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile sample
```

すでに登録済みの企画は更新され、新しい企画は追加されます。

## 4. AI/RAG用資料を投入する

Ollamaを使う場合は、先にモデルを用意してください。

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile sample
```

## 5. システムを起動する

```bash
python run.py
```

ブラウザで開く場所:

```text
http://localhost:5173
```

API確認画面:

```text
http://localhost:8000/docs
```

## 6. まず試すところ

- チャット: 「白龍の舞について教えて」「今、空いている企画は？」
- 待ち時間: カード表示、表表示、検索、並び替え
- 行程: 企画名を選んで回り方を作成
- 企画一覧: 各企画の場所、所要時間、注意事項を確認
- スタッフ: 企画IDとPINでログインして待ち時間を更新
- RAG管理: 資料投入状態と検索候補を確認
- 管理表示: ログ、モデル状態、チャット履歴リセットを確認
- 企画表示: 人気ランキング、混雑時の代替案、カテゴリ色分けを確認
- 時間/定員表示: 開始時刻、整理券、残り枠、満員表示を確認

## 7. 本番データに切り替えるとき

本番データは次に置きます。

```text
docs/data/production/exhibitions.csv
docs/data/production/knowledge.json
docs/data/production/knowledge.md
```

CSVのひな形:

```text
docs/data_template.csv
```

本番データで使うコマンド:

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile production
```

## 8. 41〜50の確認ポイント

- AIが混雑企画を聞かれたとき、近くの空いている企画を代替案として出す
- ステージや上映の企画で、開始時刻が表示・案内される
- 整理券、食券、定員、残り枠の状態が企画詳細やAI回答で使われる
- チャット初期画面で、来場者が何を相談できるか分かる
- エラー時は専門用語ではなく、来場者向けのやさしい文言になる
