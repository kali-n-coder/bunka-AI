# データ配置ルール

このフォルダでは、試作用のサンプルデータと本番用データを分けて管理します。

| フォルダ | 用途 |
| :--- | :--- |
| `docs/data/sample/` | 開発・動作確認用のサンプルデータ |
| `docs/data/production/` | 本番運用で使うデータ |

## 使うファイル

| ファイル | 役割 |
| :--- | :--- |
| `exhibitions.csv` | 企画一覧、場所、所要時間、初期待ち時間を管理するCSV |
| `knowledge.json` | AIが参照する企画説明データ |
| `knowledge.md` | AIに読ませる補足説明や自由記述の資料 |

## CSVで管理する追加情報

41〜50の改善では、画面表示やAI回答に使う情報が増えています。`exhibitions.csv` には次の情報も入れてください。

- `stage_start_time`: ステージ企画や上映企画の開始時刻。例: `10:30`
- `ticket_status`: 整理券、食券、チケットの状態。例: `整理券あり`
- `capacity_status`: 定員や残り枠の状態。例: `残りわずか`

列名と列順は [docs/data_template.csv](../data_template.csv) に合わせてください。

## 基本の流れ

サンプルで試す場合:

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile sample
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile sample
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile sample
```

本番データで試す場合:

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\seed_exhibitions_from_data.py --profile production
backend\venv\Scripts\python.exe backend\scripts\ingest_documents.py --profile production
```

本番データは `docs/data/production/exhibitions.csv` から用意してください。
