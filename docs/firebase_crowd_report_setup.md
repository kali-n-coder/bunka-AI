# Firebase 混雑報告セットアップ

来校者向け GitHub Pages から Firebase Realtime Database へ混雑報告を保存するための、Firebase CLI 前提の設定手順です。

このリポジトリでは Firebase Hosting は設定しません。来校者向けページは既存の GitHub Pages 運用を使い、Firebase CLI は Realtime Database rules のデプロイにだけ使います。

## 前提

- Firebase プロジェクトは Firebase Console で別途作成しておく。
- Realtime Database を有効化しておく。
- 本番値、API キー、サービスアカウント JSON、`.firebaserc` の実プロジェクト ID は GitHub に直書きしない。
- このリポジトリには `.firebaserc.example` だけを置く。実運用ではローカルで `.firebaserc` を作成する。

## CLI 手順

Firebase CLI が未導入の場合:

```bash
npm install -g firebase-tools
```

Firebase にログインする:

```bash
firebase login
```

サンプルからローカル用 `.firebaserc` を作る:

```bash
cp .firebaserc.example .firebaserc
```

`.firebaserc` の `your-firebase-project-id` を本番または検証用の Firebase プロジェクト ID に置き換える。`.firebaserc` は本番値を含むため、GitHub にコミットしない。

使用するプロジェクトを確認・切り替えする:

```bash
firebase use
firebase use <project-id>
```

Realtime Database rules だけをデプロイする:

```bash
firebase deploy --only database
```

## ルール概要

`database.rules.json` は `crowdReports/{exhibitionId}/{autoId}` への新規作成だけを許可します。保存できるフィールドは次の 3 つだけです。

- `status`
- `exhibitionId`
- `createdAt`

`status` は実装指示書に合わせて `empty`, `short`, `busy`, `closed` の 4 種だけを許可します。

自由記述、氏名、メールアドレス、端末情報などは保存しません。

読み取りは、現時点では本番 PC が単純に REST 取得できるように `crowdReports` だけ公開しています。保存する内容は匿名の混雑状態、企画 ID、時刻だけで、氏名や自由記述は持ちません。

より厳密に閉じる場合は、`crowdReports` の `.read` を `false` に戻し、本番 PC 側に Firebase Admin SDK や認証済みトークンを用意してください。その場合は `FIREBASE_CROWD_REPORTS_AUTH` も合わせて設定します。

## GitHub Pages との関係

`firebase.json` には Realtime Database rules の参照だけを入れています。Firebase Hosting の設定は追加していないため、既存の GitHub Pages 公開設定とは衝突しません。

GitHub Pages 側では、Actions secret に `FIREBASE_CROWD_CONFIG_JSON` を登録すると、ビルド時に `frontend/public/crowd/firebase_config.json` が生成されます。ローカルで確認するときは `frontend/public/crowd/firebase_config.sample.json` をコピーして `firebase_config.json` を作ってください。

Vite の開発サーバーで確認する場合は、`/crowd/` が React 本体に回ることがあるため、次のように直接 `index.html` を開くのが確実です。

```text
http://127.0.0.1:9001/crowd/index.html?id=32
```
