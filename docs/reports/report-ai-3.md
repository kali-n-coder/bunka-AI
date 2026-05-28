# 実装レポート 3：機能APIと行程ロジックの基礎実装 (report-ai-3.md)

## 1. 現在の状況
「白龍 AIガイドシステム」の基本機能APIを実装しました。展示情報、待ち時間、展示間の移動距離、簡易行程作成、スタッフPIN認証の入口が用意されています。

- **展示情報API**: 展示の一覧・詳細・作成・更新ができます。
- **待ち時間API**: 展示ごとの待ち時間取得・更新ができます。
- **スタッフ認証**: 簡易PIN認証を追加しました。
- **移動距離計算**: 仮の校内マップグラフを使い、展示間の推定移動時間を返せます。
- **行程プランナー**: 待ち時間・移動時間・見学時間を考慮して、簡易的な訪問順を作れます。
- **サンプル投入スクリプト**: 開発用の展示・待ち時間データをSQLiteに投入できるスクリプトを追加しました。

## 2. 現在の状況でできること
ブラウザで `http://localhost:8000/docs` を開くと、以下のAPIが増えていることを確認できます。

- `GET /api/v1/exhibitions`
- `GET /api/v1/exhibitions/{exhibition_id}`
- `POST /api/v1/exhibitions`
- `PATCH /api/v1/exhibitions/{exhibition_id}`
- `GET /api/v1/wait-times`
- `GET /api/v1/exhibitions/{exhibition_id}/wait-time`
- `POST /api/v1/exhibitions/{exhibition_id}/wait-time`
- `GET /api/v1/routes/distance`
- `POST /api/v1/routes/estimate`
- `POST /api/v1/itinerary/plan`
- `POST /api/v1/staff/login`

## 3. 追加・変更した主なファイル
- `backend/app/api/exhibitions.py`
- `backend/app/api/wait_times.py`
- `backend/app/api/routes.py`
- `backend/app/api/itinerary.py`
- `backend/app/api/staff.py`
- `backend/app/core/security.py`
- `backend/app/schemas/exhibition.py`
- `backend/app/schemas/wait_time.py`
- `backend/app/schemas/planner.py`
- `backend/app/services/map_graph.py`
- `backend/app/services/itinerary_planner.py`
- `backend/scripts/seed_exhibitions.py`
- `backend/app/main.py`
- `backend/app/core/config.py`

## 4. 検証結果
今回は時間がかかりすぎないよう、重いサーバー起動や長いE2E確認は行わず、軽量な確認だけ実施しました。

- バックエンド import 確認: 成功
- `GET /health`: 成功
- `POST /api/v1/staff/login`: 成功
- FastAPI ルート登録数確認: 成功（21ルート）

## 5. 人間が知っておくべきこと
- スタッフPINの初期値は `1234` です。
- `.env` に `STAFF_PIN=任意のPIN` を設定すれば変更できます。
- 展示や待ち時間を作成・更新するAPIでは、HTTPヘッダーに `x-staff-pin` を付ける必要があります。
- 開発用サンプルデータをSQLiteに入れるには、バックエンド環境で以下を実行します。

```bash
python backend/scripts/seed_exhibitions.py
```

## 6. 現段階の注意点
- 校内マップはまだ仮データです。
- 行程プランナーは本格的な最適化ではなく、近い展示から順に組み立てる簡易版です。
- 展示の所要時間は一律15分として扱っています。
- 待ち時間の履歴保存やスタッフごとの担当管理はまだ未実装です。
- フロントエンド画面からこれらを操作するUIはまだありません。

## 7. 次にすべきこと
- サンプルデータを投入して、`/api/v1/exhibitions` と `/api/v1/wait-times` の表示を確認する。
- 実際の展示データが揃い次第、位置情報や所要時間を反映する。
- フロントエンドに待ち時間表示、行程プランナー、スタッフ更新画面を作る。
- AIチャットから「空いている展示」「おすすめ行程」を案内できるように、DB情報との連携を強化する。

