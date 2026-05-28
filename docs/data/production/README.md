# 本番データ置き場

このフォルダには、実際に文化祭で使うデータを入れます。

最初は `docs/data_template.csv` をコピーして、次の名前で保存してください。

```text
docs/data/production/exhibitions.csv
```

AIに詳しく答えさせたい説明は、必要に応じて次のどちらかで追加します。

- `docs/data/production/knowledge.json`
- `docs/data/production/knowledge.md`

データを入れたら、以下で入力チェックできます。

```bash
backend\venv\Scripts\python.exe backend\scripts\validate_exhibition_data.py --profile production
```

## 本番前に特に確認する列

- `stage_start_time`: ステージ企画、上映企画、時間指定イベントだけ入力します。
- `ticket_status`: 整理券、食券、チケット、予約の有無を書きます。
- `capacity_status`: `通常`、`残りあり`、`残りわずか`、`満員に近い` など、来場者に見せたい状態を書きます。
- `current_wait_minutes`: 起動直後に表示される初期待ち時間です。当日はスタッフ画面から更新できます。

列名と列順は `docs/data_template.csv` と同じにしてください。
