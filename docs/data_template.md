# データ準備ガイドとひな形

このシステムで使う企画データとAI用資料の準備方法です。  
本番データを作るときは、まず [docs/data_template.csv](data_template.csv) をコピーして `docs/data/production/exhibitions.csv` として保存してください。

## 1. 企画CSV

CSVの列は次の順番で固定です。列名を変えると投入前チェックで止まります。

| 列名 | 必須 | 説明 | 例 |
| :--- | :--- | :--- | :--- |
| `name` | 必須 | 企画名 | 白龍の舞 |
| `description` | 必須 | 来場者向けの短い説明 | 光と音で白龍が空へ昇る場面を表現します。 |
| `category` | 必須 | 種類 | 展示、飲食、ステージ、体験 |
| `location_name` | 必須 | 人が読める場所名 | 体育館ステージ |
| `duration_minutes` | 必須 | 見学や利用にかかる目安時間 | 15 |
| `recommended_for` | 必須 | おすすめ対象 | 写真を撮りたい人 |
| `cautions` | 必須 | 注意事項 | フラッシュ撮影は控えてください。 |
| `stage_start_time` | 任意 | 開始時刻がある企画の時刻 | 10:30 |
| `ticket_status` | 任意 | 整理券や食券の状態 | 整理券あり、食券あり |
| `capacity_status` | 任意 | 定員や残り枠の状態 | 残りあり、満員に近い |
| `location_x` | 必須 | 仮マップ上のX座標 | 30 |
| `location_y` | 必須 | 仮マップ上のY座標 | 30 |
| `current_wait_minutes` | 必須 | 初期待ち時間 | 20 |

## 2. 入力チェック

CSVを編集したら、投入前に必ずチェックします。

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
```

チェックでは、必須項目、数値、CSV列の不足、列順、開始時刻の形式を確認します。

## 3. AI用資料

AIに詳しく答えさせたい情報は、次のどちらかに追加します。

- `docs/data/production/knowledge.json`
- `docs/data/production/knowledge.md`

企画CSVは一覧、待ち時間、行程、人気・混雑表示に使います。  
AI用資料は、チャットが説明するときの根拠として使います。
