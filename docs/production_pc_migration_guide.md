# 本番用PCへの移植ガイド

このドキュメントは、現在の開発PCから本番用PCへ白龍AIガイドを移すための手順です。  
本番PCでCodexに環境構築をお願いする場合も、このファイルを最初に読ませると進めやすいです。

## 0. 大事な前提

- 現在のPCは本番用ではありません。
- 本番DB投入、RAG本番投入、スタッフPIN生成、Firebase本番設定は本番PCで行います。
- このPCから本番PCへは、コードとデータを移します。
- `backend/venv/`、`frontend/node_modules/`、古いDB、古いChroma DBは、本番PCで作り直す方が安全です。

## 1. 本番PCに必要なもの

本番PCにインストールするもの:

- Python 3.11 以上
- Node.js 20 以上
- Git
- Ollama
- Google Chrome または Microsoft Edge
- Codex

Ollamaで必要なモデル:

```powershell
ollama pull llama3.1
ollama pull nomic-embed-text
ollama list
```

`ollama list` に次が出ればOKです。

- `llama3.1:latest`
- `nomic-embed-text:latest`

## 2. 本番PCへ移す方法

おすすめは、GitHub経由で移す方法です。

### 方法A: GitHubからcloneする

本番PCで実行します。

```powershell
cd C:\Users\任意のユーザー\Downloads
git clone <このプロジェクトのGitHub URL> hakuryu-antigravity
cd hakuryu-antigravity
```

GitHubにまだ上げていない変更がある場合は、開発PC側で先にpushしてください。

### 方法B: zipで移す

GitHubを使わない場合は、プロジェクトフォルダをzipにして本番PCへ移します。

zipに入れるもの:

- `backend/`
- `frontend/`
- `docs/`
- `run.py`
- `パンフ.pdf`
- `seitokai.md`

zipに入れなくてよいもの:

- `backend/venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `backend/sql_app.db`
- `backend/chroma_db/`
- ルート直下の `chroma_db/`

## 3. 本番PCでPython環境を作る

本番PCのプロジェクトルートで実行します。

```powershell
cd C:\Users\任意のユーザー\Downloads\hakuryu-antigravity
python -m venv backend\venv
backend\venv\Scripts\python.exe -m pip install --upgrade pip
backend\venv\Scripts\pip.exe install -r backend\requirements.txt
```

## 4. 本番PCでフロントエンド環境を作る

```powershell
cd frontend
npm install
npm run build
cd ..
```

`npm run build` が通れば、フロント側の最低確認はOKです。

## 5. 本番用データを確認する

本番データはここにあります。

```text
docs/data/production/exhibitions.csv
docs/data/production/knowledge.json
docs/data/production/knowledge.md
docs/data/production/pamphlet_unclear_items.md
```

データ検証:

```powershell
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
```

`OK` と `件数: 53` が出ればOKです。

## 6. 本番PCでDBとRAGを作る

本番PCでだけ実行します。

```powershell
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile production
```

注意:

- `seed_exhibitions_from_data.py` は企画一覧・待ち時間用DBを作ります。
- `ingest_documents.py` はAIが読むRAGデータを作ります。
- Ollamaが起動していないと `ingest_documents.py` は失敗します。

## 7. 本番用PINを作る

本番PCでだけ実行します。

```powershell
backend\venv\Scripts\python.exe backend\scripts\generate_staff_pins.py
```

生成後に確認するファイル:

```text
backend/config/staff_pins.json
```

本番では、各企画担当へ次を配布します。

- 企画名
- 企画ID
- PIN
- 待ち時間更新画面のURL
- 更新ルール

admin PINも本番用に変えてください。初期値の `1234` のまま本番運用しないでください。

## 8. 本番PCで起動する

Ollamaを起動した状態で、プロジェクトルートから実行します。

```powershell
python run.py
```

開くURL:

```text
http://localhost:5173/
```

バックエンド確認:

```text
http://localhost:8000/
```

## 9. 本番PCで最初にテストすること

### 画面

- トップ画面が開く。
- チャット画面が開く。
- 企画一覧が53件表示される。
- 待ち時間一覧が開く。
- カード表示と表表示を切り替えられる。
- admin画面はログインしないと見えない。
- スタッフ画面はログインしないと見えない。
- スタッフPINでログインした企画だけ待ち時間を更新できる。

### AI回答

試す質問:

```text
オカダナルドはどこ？
ベビすぎてカス!のアレルギーは？
今日の外ステージ予定を教えて
中ステージの閉会セレモニーは何時？
スタンプラリーはどこから始まる？
PTAは何を販売するの？
ともっちゃの料金上限は？
岩沢精神病棟はどれくらい怖い？
```

確認すること:

- 分かっている情報は正しく答える。
- PTA、ともっちゃ、岩沢精神病棟などの不明項目は、勝手に作らず「資料では確認できません」と答える。
- 緊急時や危険な内容は、スタッフ・先生確認へ誘導する。

### 待ち時間

- admin画面から任意の企画の待ち時間を変えられる。
- スタッフ画面から自分の企画だけ待ち時間を変えられる。
- 来場者画面へ変更が反映される。
- GitHub Pagesの待ち時間ページを使う場合は、Firebaseにも反映される。

## 10. 本番PCのCodexに頼むときの最初の依頼文

本番PCでCodexを開いたら、次のように依頼するとよいです。

```text
このPCを白龍AIガイドの本番用PCとしてセットアップしたいです。
まず docs/production_pc_migration_guide.md と docs/latest_operation_guide.md を読んで、現在の環境を確認してください。
その後、Python環境、Node環境、Ollamaモデル、productionデータ検証、DB投入、RAG投入、起動確認まで順番に進めてください。
ただし、破壊的な削除はしないでください。既存のDBやPINを上書きする前には必ず確認してください。
```

PIN生成まで任せる場合は、追加でこう言ってください。

```text
このPCは本番用PCです。productionデータの検証が通ったら、スタッフPINを本番用に生成してください。
生成後、backend/config/staff_pins.json の件数と企画名だけ確認して、PINの一覧は不用意に画面へ長く出さないでください。
```

## 11. 本番PCでCodexに任せる作業の順番

1. フォルダ構成を確認する。
2. Python、Node、Ollama、Gitの有無を確認する。
3. `backend/venv` を作る。
4. Python依存関係を入れる。
5. `frontend/npm install` と `npm run build` を通す。
6. Ollamaモデルを確認する。
7. `validate_exhibition_data.py --profile production` を通す。
8. `seed_exhibitions_from_data.py --profile production` を実行する。
9. `ingest_documents.py --profile production` を実行する。
10. 必要なら本番用PINを生成する。
11. `python run.py` で起動する。
12. ブラウザで `http://localhost:5173/` を確認する。
13. AI回答、待ち時間更新、admin、スタッフログインをテストする。

## 12. よくある詰まりポイント

### `ModuleNotFoundError: No module named 'app'`

スクリプトの実行場所やPythonパスがずれている可能性があります。  
プロジェクトルートから、次の形で実行してください。

```powershell
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
```

### Ollamaの `/api/chat` が404になる

Ollama本体が古い、またはAPI差分がある可能性があります。  
`ollama list` と `ollama --version` を確認してください。

### 検索モデルが「確認が必要」になる

`nomic-embed-text` がOllamaに入っているか、Ollamaが起動しているかを確認してください。

```powershell
ollama list
ollama pull nomic-embed-text
```

### 画面が真っ白

まずフロントのビルドを確認します。

```powershell
cd frontend
npm install
npm run build
cd ..
```

その後、`python run.py` を再起動してください。

## 13. 本番PCへ移す前にこのPCでやっておくこと

- 最新変更をGitHubへpushする、またはzipにまとめる。
- `docs/data/production/exhibitions.csv` が53件であることを確認する。
- `docs/data/production/knowledge.json` が53件であることを確認する。
- `docs/data/production/pamphlet_unclear_items.md` の不明項目が整理済みであることを確認する。
- 本番PCで使うGitHub Pages待ち時間ページ、Firebase設定、QRコードの扱いを決める。

## 14. 本番当日までに決めること

- 本番PCをどこに置くか。
- 来場者用PCまたはタブレットをどこに置くか。
- adminを触れる人は誰か。
- 各企画の待ち時間を誰が更新するか。
- スタッフPINを誰が配るか。
- GitHub Pagesの待ち時間QRをどこに掲示するか。
- AIチャットを来場者に自由入力させるか、スタッフ近くの端末だけにするか。
- トラブル時に誰へ連絡するか。
