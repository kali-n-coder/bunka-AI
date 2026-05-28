# 白龍AIガイド 最新運用ガイド

このガイドは、サンプル運用から本番データ運用までに必要な「データの置き場所」「更新方法」「起動方法」「確認する画面」をまとめた最新版です。

注意: 現在作業しているPCは本番用ではありません。このPCではデータ編集、検証、画面確認までに留め、本番DB投入、RAG本番投入、スタッフPIN生成、Firebase本番設定は本番PCで実行してください。

## 1. 用意するデータ

本番用データは次の場所に置きます。

| 用途 | ファイル | 形式 |
| :--- | :--- | :--- |
| 企画一覧、場所、待ち時間初期値 | `docs/data/production/exhibitions.csv` | CSV |
| AIが読む企画説明 | `docs/data/production/knowledge.json` | JSON |
| AIが読む補足資料 | `docs/data/production/knowledge.md` | Markdown |
| スタッフ用PIN | `backend/config/staff_pins.json` | JSON |

サンプルで試す場合は `production` の代わりに `sample` を使います。

## 2. 企画CSV

ひな形は次のファイルです。

```text
docs/data_template.csv
```

列はこの順番で使います。

```csv
name,description,category,location_name,duration_minutes,recommended_for,cautions,stage_start_time,ticket_status,capacity_status,location_x,location_y,current_wait_minutes
```

主な入力内容:

| 列名 | 入れる内容 |
| :--- | :--- |
| `name` | 企画名 |
| `description` | 来場者向けの短い説明 |
| `category` | 展示、飲食、ステージ、体験、案内など |
| `location_name` | 本館2階 2-A教室、体育館ステージなど |
| `duration_minutes` | 見学や利用にかかる目安時間 |
| `recommended_for` | 小学生向け、写真を撮りたい人向けなど |
| `cautions` | 撮影禁止、整理券あり、飲食不可など |
| `stage_start_time` | ステージ開始時刻。なければ空欄 |
| `ticket_status` | 整理券あり、整理券なし、売り切れ次第終了など |
| `capacity_status` | 通常、残りあり、満員に近いなど |
| `location_x`, `location_y` | 仮マップ用の座標 |
| `current_wait_minutes` | 起動時の初期待ち時間 |

企画が100件近くある場合も、このCSVに1行ずつ追加します。

## 3. AI用データ

AIに正確に答えさせたい内容は、CSVだけでなく `knowledge.json` と `knowledge.md` にも入れます。

`knowledge.json` は企画ごとの説明に向いています。

```json
[
  {
    "name": "白龍の舞",
    "description": "光と音で白龍が空へ昇る場面を表現する演出展示です。",
    "category": "展示",
    "location_name": "体育館ステージ",
    "duration_minutes": 15,
    "recommended_for": "演出展示を見たい人、写真を撮りたい人",
    "cautions": "フラッシュ撮影は控えてください。",
    "stage_start_time": "10:30",
    "ticket_status": "整理券なし",
    "capacity_status": "通常"
  }
]
```

`knowledge.md` は全体案内、当日の注意、ルール、よくある質問などに向いています。

## 4. データ更新手順

本番データを更新したら、本番PCのプロジェクトルートで次を実行します。このPCでは、基本的に検証コマンドまでにしてください。

```powershell
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile production
```

サンプルで試す場合:

```powershell
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile sample
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile sample
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile sample
```

## 5. PIN管理

admin PINは管理画面に入るためのPINです。初期値は `1234` です。

本番前は `.env` などで `STAFF_PIN` を変更してください。現在の実装では admin PIN と全体管理用PINに同じ設定値を使っています。

スタッフPINは企画ごとに分かれています。スタッフ画面では、自分の企画IDとPINでログインした企画の待ち時間だけ更新できます。

企画追加後にPINを生成し直す場合:

```powershell
backend\venv\Scripts\python.exe backend\scripts\generate_staff_pins.py
```

本番用PINの生成・配布は本番PCで行ってください。このPCの `staff_pins.json` は本番配布用として扱わないでください。

admin画面からも、全企画のスタッフPINを確認・変更できます。

## 6. 起動方法

Ollamaのモデルを用意します。

```powershell
ollama pull llama3.1
ollama pull nomic-embed-text
```

システムを起動します。

```powershell
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

## 7. 画面の使い方

左メニューの主な画面:

- `白龍に相談`: AIチャット
- `待ち時間を見る`: 待ち時間一覧、カード表示、表表示、ランキング、代替案
- `行程を作る`: 企画を選んで回り方を作成
- `企画一覧`: 企画詳細、場所、所要時間、注意事項

スタッフ画面とadmin画面は目立たない入口にしています。

- `スタッフ`: 左下の小さいリンクから開く
- `admin`: 左下の小さいリンクから開く

## 8. admin画面

admin画面は、ログインしないと中身を見られません。

左下の小さい `admin` リンクを開き、admin PINを入力してください。初期値は `1234` です。

ログイン後にできること:

- `運用状態`: 回答モデル、検索モデル、RAG投入件数、直近ログの確認
- `RAG管理`: 資料ファイル数、読み込み候補、投入済み件数、検索候補の確認
- `全待ち時間`: すべての企画の待ち時間を管理者として更新
- `PIN管理`: すべての企画のスタッフPINを確認・変更

admin画面を使い終わったら、画面右上の `ログアウト` を押します。

## 9. 最低限テストするところ

### 画面表示

- `http://localhost:5173` が真っ白ではなく表示される
- チャット、待ち時間、行程、企画一覧が開ける
- 左下の小さい `スタッフ` と `admin` が開ける
- adminはPINを入れるまで管理内容が見えない

### データ表示

- 企画一覧にCSVの企画が表示される
- 場所、所要時間、注意事項、整理券、定員情報が表示される
- 待ち時間一覧でカード表示と表表示を切り替えられる
- 待ち時間の検索、並び替え、代替案が動く

### AI回答

試す質問:

```text
白龍の舞について教えて
今、空いている企画は？
おすすめの回り方は？
体育館ステージはどこ？
整理券が必要な企画は？
```

確認すること:

- 資料に基づいて答えている
- 資料にないことを作りすぎていない
- 待ち時間を使った案内ができる
- 回答下に参照資料が表示される

### スタッフ更新

- スタッフ画面で企画IDとPINでログインできる
- ログインした企画名が表示される
- その企画の待ち時間だけ更新できる
- 更新後、待ち時間一覧にも反映される

### admin更新

- admin PINでログインできる
- 全企画の待ち時間を更新できる
- スタッフPINを変更できる
- 変更したPINでスタッフログインできる
- ログアウト後はadmin内容が見えない

## 10. よくあるトラブル

### 検索モデルが「確認が必要」になる

`ollama list` で `nomic-embed-text:latest` が出ているか確認してください。

```powershell
ollama list
```

出ていない場合:

```powershell
ollama pull nomic-embed-text
```

出ているのに変わらない場合は、バックエンドを再起動してからadmin画面の `状態更新` を押してください。

### AIが502になる

Ollamaが起動しているか、回答モデルが入っているか確認します。

```powershell
ollama list
ollama pull llama3.1
```

その後、`python run.py` を再起動します。

### データを変えたのに反映されない

CSVだけ変えた場合は、本番PCで `seed_exhibitions_from_data.py` を実行します。AI回答用データも変えた場合は、本番PCで `ingest_documents.py` も実行します。

```powershell
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile production
```
