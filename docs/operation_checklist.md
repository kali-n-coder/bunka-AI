# 白龍AIガイド 当日運用チェックリスト

設置PCで来場者に触ってもらう前に、上から順番に確認してください。

## 1. 起動前

- 設置PCの電源が入っている
- プロジェクトフォルダを開ける
- `backend\venv` がある
- Ollamaを使う場合、Ollamaアプリが起動している
- `ollama list` で `llama3.1:latest` と `nomic-embed-text:latest` が見える

## 2. データ確認

サンプルで確認する場合:

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile sample
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile sample
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile sample
```

本番データで確認する場合:

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile production
```

## 3. 起動

```bash
python run.py
```

確認するURL:

- 来場者画面: `http://localhost:5173`
- API確認画面: `http://localhost:8000/docs`

## 4. 来場者画面

- 画面が真っ白ではない
- 左メニューが表示される
- 「白龍に相談する」「待ち時間を見る」「行程を作る」「企画一覧」が開ける
- エラー時も専門用語ではなく、やさしい案内文が表示される

## 5. 待ち時間

- カード表示と表表示を切り替えられる
- 検索できる
- 待ち時間順、カテゴリ順で並び替えられる
- 更新ボタンで最新状態を取り直せる

## 6. スタッフ更新

- 左下の小さな「スタッフ」から画面を開ける
- 企画IDとPINでログインできる
- ログイン後、自分の企画名が表示される
- その企画の待ち時間だけ更新できる
- 更新後、何分に更新したか確認メッセージが出る

## 7. 行程・企画一覧

- 行程は企画名から選べる
- カテゴリ、開始地点、終了地点を指定できる
- 合計時間、移動時間、待ち時間、見学時間が表示される
- 企画一覧から詳細を確認できる

## 8. AI回答

確認する質問例:

- 白龍の舞について教えて
- 今、空いている企画は？
- おすすめの回り方は？
- 体育館はどこ？

確認すること:

- 資料に基づいた回答になっている
- 待ち時間の質問では最新待ち時間を使っている
- 資料にないことを作りすぎていない
- 回答下に参照資料が表示される

## 9. 管理・状態確認

- 管理者向けのログ表示で、チャットエラーやRAG検索失敗を確認できる
- モデル状態表示で、回答モデルとEmbeddingモデルが正常か確認できる
- RAG管理で、資料件数、投入済み件数、検索結果を確認できる
- 必要な場合にチャット履歴をリセットできる
- リロード後のチャット履歴の扱いが、当日の運用方針と合っている

## 10. 企画表示・当日案内

- 人気ランキングが表示される
- 混雑している企画に対して、近くの空いている代替案が出る
- カテゴリごとの色分けで、飲食、展示、ステージ、体験などを区別できる
- ステージ企画や上映企画の開始時刻が表示される
- 整理券、食券、定員、残り枠、満員状態が表示される
- チャット初期画面で、来場者が相談できる内容が分かる

## 11. トラブル時

画面が真っ白:

- `python run.py` が動いているか確認
- `http://localhost:5173` を開き直す
- ブラウザを更新する

AIが答えない:

- Ollamaが起動しているか確認
- `ollama list` でモデルがあるか確認
- RAGデータ投入済みか確認

待ち時間がサンプル表示:

- バックエンドが起動しているか確認
- `seed_exhibitions_from_data.py` を実行したか確認
- `http://localhost:8000/docs` が開けるか確認
