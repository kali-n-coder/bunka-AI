# 来校者混雑報告機能 実装指示書

この指示書は、別のCodex・別フォルダで「来校者による混雑報告機能」を実装するためのものです。  
本番PCセットアップやLM Studio移行とは作業を分け、混ざらないようにしてください。

## 0. この作業の目的

クラス企画担当が忙しく、待ち時間を手入力する運用が難しいため、来校者のスマホから匿名で混雑状況を報告してもらいます。

ただし、来校者は学校Wi-Fiを使えず、校内LAN上の白龍AIガイド本体へ直接アクセスできません。  
そのため、来校者向け入力ページは外部公開できる **GitHub Pages** に置き、入力内容は **Firebase Realtime Database** に保存します。

本番PC側の白龍AIガイドは、Firebaseから1分に1回ほど報告を取得し、設置タブレット・PCの画面に「混雑目安」として表示します。

## 1. 全体構成

```text
来校者スマホ
  ↓ 外部回線
GitHub Pagesの混雑報告ページ
  ↓
Firebase Realtime Databaseに保存
  ↓ 1分に1回
本番PC側の白龍AIガイドがFirebaseから取得
  ↓
設置タブレット・PCの画面に混雑目安として表示
```

重要:

- 来校者スマホから本番PCへ直接アクセスさせない。
- 本番PCを外部公開しない。
- 来校者入力は「正確な待ち時間」ではなく「混雑目安」として扱う。
- 実装は既存のスタッフ待ち時間更新機能を壊さず、追加機能として入れる。

## 2. 参照するドキュメント

まず以下を読んでください。

```text
docs/visitor_wait_time_contribution_plan.md
docs/github_pages_wait_times.md
docs/latest_operation_guide.md
docs/production_pc_migration_guide.md
```

必要なら以下も確認してください。

```text
frontend/public/wait/
backend/app/services/public_wait_sync.py
backend/app/api/wait_times.py
backend/app/api/admin.py
frontend/src/App.tsx
frontend/src/api/client.ts
```

## 3. 作業する場所

別フォルダでcloneして作業してください。

例:

```powershell
cd C:\Users\sherl\Downloads
git clone https://github.com/kali-n-coder/bunka-AI.git bunka-AI-crowd
cd bunka-AI-crowd
```

ブランチを分けてください。

```powershell
git checkout -b feature/visitor-crowd-reports
```

## 4. 実装対象

実装対象は大きく3つです。

1. GitHub Pages側の来校者入力ページ
2. Firebase Realtime Databaseへの保存
3. 本番PC側でFirebaseから取得して表示

## 5. 実装しないこと

この作業では以下はやらないでください。

- LM Studio移行
- Ollama設定変更
- 本番PCセットアップ
- 本番PIN生成
- 既存DBの破壊的削除
- スタッフ待ち時間更新機能の削除
- AIプロンプトの大幅変更
- 自由記述コメント欄の追加
- 名前、学年、クラス、位置情報などの個人情報収集

## 6. GitHub Pages側の実装

### 6.1 追加するページ

以下のような専用ページを作ってください。

```text
frontend/public/crowd/index.html
frontend/public/crowd/crowd.css
frontend/public/crowd/crowd.js
frontend/public/crowd/firebase_config.sample.json
```

既存の `frontend/public/wait/` と同じように、Viteアプリ本体とは独立した静的ページとして作るのがよいです。

### 6.2 画面要件

来校者向け画面に必要なもの:

- タイトル: `混雑報告`
- 説明: `近くで見た範囲で、いまの混み具合を教えてください。`
- 企画選択
- 4択ボタン
- 送信ボタン、または4択を押したら即送信
- 送信完了メッセージ
- 注意文

4択:

```text
すぐ入れそう
少し待つ
かなり混んでいる
受付停止・満員っぽい
```

内部値:

```text
empty
short
busy
closed
```

注意文:

```text
報告は匿名で、混雑目安として使われます。
正確でなくても大丈夫です。
実際の待ち時間や受付状況は現地の案内を確認してください。
```

### 6.3 企画一覧データ

GitHub Pagesはバックエンドに直接アクセスできない前提です。  
そのため、静的な企画一覧JSONを置いてください。

候補:

```text
frontend/public/crowd/exhibitions.json
```

内容は `docs/data/production/exhibitions.csv` から必要項目だけ変換します。

必要項目:

```json
[
  {
    "id": 32,
    "name": "オカダナルド",
    "category": "飲食",
    "location_name": "屋外 3-F"
  }
]
```

注意:

- DB上のIDとCSVの行番号がずれる可能性があるため、実装時に現在のDB IDルールを確認すること。
- 簡易実装ではCSV順を1始まりのIDとして扱ってよいが、本番DBのIDと合わせる必要がある。

### 6.4 URLパラメータ対応

企画別QRも将来使えるように、URLパラメータを受け取れるようにしてください。

例:

```text
/crowd/?id=32
```

この場合:

- `id=32` の企画を初期選択する。
- 企画選択欄を固定してもよい。
- 不正なIDの場合は通常の企画選択画面に戻す。

### 6.5 デザイン方針

来校者がスマホで使うため、PC向けではなくスマホ優先にしてください。

要件:

- ボタンは大きくする。
- 文字は小さくしすぎない。
- 片手でも押しやすい。
- 白背景または薄いグレー背景。
- 4択はカード型ボタン。
- 送信完了が分かりやすい。

## 7. Firebase保存

### 7.1 保存先

Firebase Realtime Databaseを使います。

推奨パス:

```text
crowdReports/{exhibitionId}/{autoId}
```

保存例:

```json
{
  "exhibitionId": 32,
  "status": "busy",
  "createdAt": 1710000000000
}
```

### 7.2 保存するもの

保存するもの:

- `exhibitionId`
- `status`
- `createdAt`

保存しないもの:

- 名前
- 学年
- クラス
- メールアドレス
- 電話番号
- 位置情報
- 自由記述コメント

### 7.3 Firebase設定ファイル

本番値はGitHubに直書きしないでください。  
サンプルファイルだけ置きます。

```text
frontend/public/crowd/firebase_config.sample.json
```

例:

```json
{
  "databaseURL": "https://your-project-default-rtdb.firebaseio.com"
}
```

実運用では、GitHub Pagesに配置される `firebase_config.json` を別途用意する想定です。

### 7.4 Firebaseルール

最低限、保存形式を制限してください。

方針:

- `crowdReports` にだけ書ける。
- `status` は `empty`, `short`, `busy`, `closed` のどれか。
- `exhibitionId` は数値。
- `createdAt` は数値。
- 自由記述は受け付けない。

ルールの例はドキュメントに残してください。  
実際のFirebase設定は、本番環境で確認しながら行います。

## 8. 本番PC側の取得

### 8.1 バックエンド設定

`.env` でFirebaseのURLを設定できるようにしてください。

既存の `FIREBASE_WAIT_TIMES_URL` がある場合、それを流用するか、新しく分けるか検討してください。

新規に分ける場合の例:

```env
FIREBASE_CROWD_REPORTS_URL=https://your-project-default-rtdb.firebaseio.com/crowdReports.json
FIREBASE_CROWD_REPORTS_AUTH=
FIREBASE_CROWD_SYNC_INTERVAL_SECONDS=60
```

### 8.2 取得処理

本番PC側で、Firebaseから報告を取得して集計します。

候補ファイル:

```text
backend/app/services/crowd_report_sync.py
```

処理:

1. Firebaseから `crowdReports` を取得する。
2. 直近15分以内の報告だけ使う。
3. 企画ごとに集計する。
4. `visitor_crowd_status`, `visitor_report_count`, `visitor_last_reported_at` のような情報を作る。
5. APIや画面から参照できるようにする。

### 8.3 集計方法

最初は単純でよいです。

数値化:

```text
empty = 0
short = 1
busy = 2
closed = 3
```

集計:

- 直近15分の報告を集める。
- 最も多いstatusを採用する。
- 同数の場合は新しい報告に近いもの、または混んでいる方を採用する。

表示用:

```text
empty  -> すぐ入れそう
short  -> 少し待つかも
busy   -> かなり混んでいる
closed -> 受付停止・満員っぽい
```

報告がない場合:

```text
情報なし
```

古い場合:

```text
情報が古いです
```

### 8.4 1分ごとの同期

本番PC側の同期は1分に1回で十分です。

方法:

- FastAPI起動時にバックグラウンドタスクとして開始する。
- または、APIアクセス時に必要に応じてキャッシュ更新する。
- 実装が複雑なら、最初は手動更新APIでもよい。

最初の実装では、壊れにくさを優先してください。

## 9. API設計案

### 9.1 来校者報告集計API

設置タブレット・PCの画面が参照するAPIです。

```text
GET /api/v1/crowd-reports/summary
```

レスポンス例:

```json
[
  {
    "exhibition_id": 32,
    "status": "busy",
    "label": "かなり混んでいる",
    "report_count": 8,
    "last_reported_at": "2026-06-01T10:15:00+09:00",
    "source": "visitor"
  }
]
```

### 9.2 手動同期API

admin画面から手動更新できると便利です。

```text
POST /api/v1/admin/crowd-reports/sync
```

## 10. フロントエンド表示

既存の待ち時間一覧に、来校者報告を追加表示します。

表示例:

```text
オカダナルド
スタッフ更新: なし
来校者報告: かなり混んでいる
最近の報告: 8件
最終報告: 3分前
```

スタッフ入力がある場合:

```text
オカダナルド
スタッフ更新: 20分
来校者報告: かなり混んでいる
最近の報告: 8件
最終報告: 3分前
```

スタッフ入力と来校者報告が食い違っても、片方を消さないでください。  
どちらも表示し、「目安」であることを明記します。

## 11. admin画面

admin画面に、来校者報告の一覧を追加します。

表示項目:

```text
企画名
来校者報告
報告数
最終報告
```

あると便利なボタン:

```text
Firebaseから今すぐ取得
```

## 12. AI連携

余裕があれば、AI回答にも来校者報告を使えるようにします。

例:

```text
今混んでいる企画は？
```

回答例:

```text
来校者報告では、オカダナルドがかなり混んでいるようです。
ただし目安なので、現地の案内も確認してください。
```

AIに渡す場合も、必ず「来校者報告による目安」として扱ってください。

## 13. 完了条件

最低限の完了条件:

- GitHub Pages用の `crowd` ページがある。
- 企画を選べる。
- 4択で混雑報告を送信できる。
- Firebase Realtime Databaseに保存される。
- 本番PC側バックエンドがFirebaseから報告を取得できる。
- 直近報告を企画ごとに集計できる。
- 待ち時間一覧に来校者報告が表示される。
- admin画面で来校者報告を確認できる。
- 自由記述や個人情報を保存していない。
- 既存のスタッフ待ち時間更新機能が壊れていない。

## 14. テスト項目

### GitHub Pages側

- 企画一覧が表示される。
- 企画を選択できる。
- URL `?id=32` で初期選択できる。
- 4択ボタンを押せる。
- Firebaseへ保存される。
- 送信後に完了メッセージが出る。
- スマホ幅でボタンが押しやすい。

### Firebase

- `crowdReports/{exhibitionId}/{autoId}` に保存される。
- `status` が4種類以外にならない。
- 自由記述が保存されない。
- 個人情報が保存されない。

### 本番PC側

- Firebaseから取得できる。
- 直近15分のみ集計される。
- 報告なしの場合に落ちない。
- Firebase未設定でもシステム全体が落ちない。
- 待ち時間一覧に表示される。
- admin画面に表示される。
- 既存のチャット、企画一覧、スタッフ画面が壊れていない。

## 15. 本番前に確認すること

- Firebaseプロジェクトを本番用にする。
- GitHub PagesのURLを確定する。
- QRコードを作る。
- QRコードを掲示する場所を決める。
- 来校者向けポスターの文言に「混雑報告」案内を追加するか決める。
- 本番PCがFirebaseへアクセスできるか確認する。
- 設置タブレット・PCの表示に来校者報告が出るか確認する。

## 16. 別Codexへの最初の依頼文

別フォルダでCodexを立てたら、次を貼ってください。

```text
来校者による混雑報告機能を実装したいです。

まず docs/crowd_report_implementation_brief.md と docs/visitor_wait_time_contribution_plan.md を読んで、目的と制約を理解してください。

重要な制約:
- 来校者は学校Wi-Fiを使えないため、本番PCへ直接アクセスできません。
- 来校者入力ページはGitHub Pagesに置きます。
- 入力内容はFirebase Realtime Databaseへ保存します。
- 本番PC側の白龍AIガイドが1分に1回Firebaseから取得します。
- 表示は正確な待ち時間ではなく、来校者報告による混雑目安です。
- 自由記述や個人情報は保存しません。
- LM Studio移行、本番PCセットアップ、本番PIN生成はこの作業では触らないでください。

まず実装計画を短く出したあと、実装を進めてください。
```
