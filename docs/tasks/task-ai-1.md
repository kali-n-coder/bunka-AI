# タスク細分化：1. システム基盤の実装 (task-ai-1.md)

このドキュメントは `task-ai.md` の「1. システム基盤の実装」を詳細に分解したものです。

## 1.1 バックエンド (FastAPI) の構築
- [ ] `backend/` ディレクトリの作成と初期化
- [ ] 依存ライブラリの定義 (`requirements.txt` または `pyproject.toml`)
    - FastAPI, Uvicorn, SQLAlchemy, Pydantic, python-dotenv 等
- [ ] プロジェクト構造の展開
    - `app/main.py`: エントリーポイント
    - `app/api/`: エンドポイント定義
    - `app/core/`: 設定 (config) やセキュリティ
    - `app/models/`: DBモデル
    - `app/schemas/`: Pydanticモデル
    - `app/services/`: ビジネスロジック
- [ ] CORS (Cross-Origin Resource Sharing) の設定
- [ ] グローバルな例外ハンドラーの実装
- [ ] 環境変数管理 (`.env` 読み込み) の実装

## 1.2 フロントエンド (React + Vite) の構築
- [ ] `frontend/` ディレクトリにて Vite (React + TypeScript) プロジェクトを初期化
- [ ] 必要なライブラリのインストール
    - React Router, Axios (または Fetch API), Lucide React (アイコン) 等
- [ ] プロジェクト構造の展開
    - `src/api/`: バックエンド通信用クライアント
    - `src/components/`: 共通パーツ
    - `src/pages/`: 画面単位のコンポーネント
    - `src/hooks/`: カスタムフック
    - `src/types/`: TypeScript型定義
- [ ] 基本的なルーティング (React Router) の設定
- [ ] 環境変数設定 (`.env.local`) と Vite への統合

## 1.3 データベース (SQLite) と ORM 設定
- [ ] `database.py` の作成 (SQLAlchemy エンジン・セッション設定)
- [ ] 共通 Base クラスの定義
- [ ] 初期スキーマのモデル定義
    - `Exhibition`: 展示物情報（ID, 名前, 説明, 位置等）
    - `WaitTime`: 待ち時間データ（展示物ID, 現在の待ち時間, 更新日時）
- [ ] Alembic の初期化と設定
- [ ] 初回マイグレーションファイルの生成と適用
- [ ] データベース接続確認用のテストスクリプト作成

## 1.4 Ollama API クライアントの実装
- [ ] `app/services/ollama_client.py` の作成
- [ ] Ollama API との通信用 HTTP クライアントの実装
- [ ] モデル指定、パラメータ (temperature等) の設定機能
- [ ] チャット履歴を保持・送信するロジックの実装
- [ ] ストリーミングレスポンスを受け取るためのジェネレータ関数の実装
- [ ] 接続エラー時の例外処理とログ出力

## 1.5 システム統合起動スクリプトの作成
- [ ] ルートディレクトリに `run.py` を作成
- [ ] Python からバックエンド (Uvicorn) とフロントエンド (Vite) を並行起動するロジック
- [ ] 依存関係（Node.js, Pythonライブラリ）の有無を確認するプリチェック機能
- [ ] `.env` ファイルの存在確認とテンプレートからの自動生成機能（オプション）
- [ ] 起動時の簡易サマリー表示（URL, ログの出力場所等）
