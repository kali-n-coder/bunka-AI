# GitHub Pages用 待ち時間公開ガイド

待ち時間だけをスマホから見られるようにするための軽量ページを追加しました。

公開ページ本体:

```text
frontend/public/wait/
```

ローカルで確認するURL:

```text
http://localhost:5173/wait/
```

GitHub Pagesで公開した後のURL例:

```text
https://ユーザー名.github.io/リポジトリ名/wait/
```

## 1. 画面でできること

- スマホ向けに待ち時間一覧を表示
- 30秒ごとに自動更新
- 企画名、場所、カテゴリで検索
- カテゴリで絞り込み
- 空いている企画数、企画数、最長待ち時間を表示
- Firebase未設定でもサンプルデータで表示確認

## 2. Firebaseで用意するもの

Firebaseでは Realtime Database を使う想定です。

用意するデータの置き場所:

```text
publicWaitTimes
```

データ形式は配列です。

```json
[
  {
    "id": 1,
    "exhibition_id": 1,
    "exhibition_name": "白龍の舞",
    "category": "展示",
    "location_name": "体育館ステージ",
    "duration_minutes": 15,
    "current_wait_minutes": 20,
    "ticket_status": "整理券なし",
    "capacity_status": "通常",
    "updated_at": "2026-05-11T09:00:00"
  }
]
```

## 3. Firebase読み取り設定

`frontend/public/wait/firebase_config.json` を作成します。

ひな形:

```text
frontend/public/wait/firebase_config.sample.json
```

作成する内容:

```json
{
  "mode": "firebase-rtdb",
  "databaseUrl": "https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com",
  "path": "publicWaitTimes"
}
```

このファイルはWebに公開されます。APIキーや管理者用の秘密情報は入れないでください。

## 4. Firebaseルール

GitHub Pagesから誰でも読める必要があるため、少なくとも `publicWaitTimes` は公開読み取りにします。

最小例:

```json
{
  "rules": {
    "publicWaitTimes": {
      ".read": true,
      ".write": false
    }
  }
}
```

書き込みはブラウザから直接行わず、PC上で動いているこのシステムのバックエンドから送る想定です。

## 5. バックエンドからFirebaseへ送る設定

`backend/.env` に次を追加します。

```env
FIREBASE_WAIT_TIMES_URL=https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com/publicWaitTimes.json
```

認証つきRESTで送る場合だけ、必要に応じて次も追加します。

```env
FIREBASE_WAIT_TIMES_AUTH=YOUR_TOKEN
```

未設定の場合、ローカルのスタッフ画面やadmin画面は今まで通り動きますが、GitHub Pages側には反映されません。

## 6. 更新の流れ

1. `python run.py` でPC用システムを起動します。
2. スタッフ画面またはadmin画面で待ち時間を更新します。
3. `FIREBASE_WAIT_TIMES_URL` が設定されていれば、更新後に待ち時間一覧がFirebaseへ送信されます。
4. スマホ側の `/wait/` ページはFirebaseを30秒ごとに読み直します。

admin画面の `公開待ち時間を送信` ボタンを押すと、現在の全待ち時間を手動でFirebaseへ送れます。

## 7. GitHub Pagesへの反映

このリポジトリをGitHubに置いたら、次のワークフローが使えます。

```text
.github/workflows/deploy-wait-pages.yml
```

GitHub側でやること:

1. リポジトリの `Settings` を開く
2. `Pages` のSourceを `GitHub Actions` にする
3. `Settings` -> `Secrets and variables` -> `Actions` に `FIREBASE_WAIT_CONFIG_JSON` を追加する
4. `main` ブランチへpushする

`FIREBASE_WAIT_CONFIG_JSON` の中身:

```json
{"mode":"firebase-rtdb","databaseUrl":"https://YOUR_PROJECT_ID-default-rtdb.firebaseio.com","path":"publicWaitTimes"}
```

## 8. まだGitリポジトリではない場合

現在のフォルダがGitリポジトリではない場合は、GitHub Desktopでこのフォルダをリポジトリ化してからGitHubへ公開するのが一番簡単です。

コマンドでやる場合:

```powershell
git init
git add .
git commit -m "Add public wait-time page"
git branch -M main
git remote add origin https://github.com/ユーザー名/リポジトリ名.git
git push -u origin main
```

すでに別の場所にGitリポジトリがある場合は、この変更一式をそちらへ移してからpushしてください。

## 9. テスト項目

- `http://localhost:5173/wait/` がスマホ幅でも見やすい
- 検索とカテゴリ絞り込みが動く
- Firebase未設定時にサンプルが表示される
- `firebase_config.json` 設定後にFirebaseのデータが表示される
- スタッフ画面で待ち時間を更新したあと、Firebaseの `publicWaitTimes` が更新される
- GitHub Pagesの `/wait/` をスマホで開ける
