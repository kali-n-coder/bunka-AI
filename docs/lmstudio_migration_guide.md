# LM Studio移行ガイド

このドキュメントは、本番用PCで白龍AIガイドのAI実行基盤を **Ollama から LM Studio に切り替える** ための手順です。  
GPUの都合でOllamaよりLM Studioの方が安定する場合、本番PCではこのガイドを優先してください。

## 0. 結論

現在の白龍AIガイドは、コード上ではOllama APIを直接呼んでいます。

現在の主な接続先:

- チャット: `http://localhost:11434/api/chat`
- 生成フォールバック: `http://localhost:11434/api/generate`
- Embedding: `http://localhost:11434/api/embeddings`

LM StudioはOpenAI互換APIとして使うのが基本です。

LM Studioの主な接続先:

- モデル一覧: `http://localhost:1234/v1/models`
- チャット: `http://localhost:1234/v1/chat/completions`
- Embedding: `http://localhost:1234/v1/embeddings`

そのため、本番PCでは次の対応が必要です。

1. LM Studioをインストールする。
2. LM Studioで回答用モデルをダウンロード・ロードする。
3. 必要ならEmbedding用モデルもダウンロード・ロードする。
4. LM StudioのLocal Serverを起動する。
5. バックエンドのAI接続クライアントをOpenAI互換API用に変更する。
6. `.env` でLM Studio用のURLとモデル名を設定する。
7. RAG投入とチャット確認をやり直す。

## 1. 参考情報

LM Studioの公式ドキュメントでは、OpenAI互換APIとしてChat、Responses、Embeddingsなどを提供すると説明されています。  
LM StudioのOpenAI互換エンドポイントは、通常 `http://localhost:1234/v1` をベースURLとして使います。

参考:

- LM Studio Developer Docs: https://lmstudio.ai/docs/api/
- OpenAI Compatibility Endpoints: https://lmstudio.ai/docs/app/api/endpoints/openai

## 2. 本番PCに入れるもの

本番PCにインストールするもの:

- LM Studio
- Python 3.11以上
- Node.js 20以上
- Git
- Codex

Ollamaは不要にできます。  
ただし、移行中に比較確認したい場合だけ残しても構いません。

## 3. LM Studio側の準備

### 3.1 回答用モデル

LM Studioで、チャットに使うモデルを1つロードしてください。

おすすめの考え方:

- 本番PCのGPU VRAMに収まるモデルを選ぶ。
- 日本語がある程度できるモデルを選ぶ。
- 重すぎるモデルより、安定して数秒〜十数秒で返るモデルを優先する。

候補例:

- Qwen系の日本語に強いモデル
- Llama系の軽量Instructモデル
- Gemma系の軽量Instructモデル

モデル名はLM StudioのLocal Server画面、または `GET /v1/models` で確認します。

確認コマンド:

```powershell
curl http://localhost:1234/v1/models
```

### 3.2 Embedding用モデル

RAG検索にはEmbeddingモデルが必要です。  
LM StudioでEmbedding対応モデルを使える場合は、Embeddingモデルもロードしてください。

候補例:

- Nomic Embed系
- BGE系
- E5系

注意:

- チャット用モデルとEmbedding用モデルは別でよいです。
- LM StudioでEmbeddingモデルが使えない場合、RAG投入ができません。
- その場合は、暫定的に「回答はLM Studio、EmbeddingだけOllama」の混在運用も可能ですが、本番では管理が複雑になります。

Embedding確認コマンド:

```powershell
curl http://localhost:1234/v1/embeddings `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"ここにEmbeddingモデル名\",\"input\":\"白龍祭の案内テスト\"}"
```

返答に `data[0].embedding` のような配列があればOKです。

## 4. LM Studio Local Serverの起動

LM Studioで次を行います。

1. LM Studioを開く。
2. 回答用モデルをロードする。
3. 必要ならEmbedding用モデルもロードする。
4. `Developer` または `Local Server` の画面を開く。
5. ServerをStartする。
6. Portが `1234` になっていることを確認する。

同じPC内だけで使うなら、通常は `localhost` のままでOKです。  
別PCやタブレットから直接LM Studio APIへアクセスさせる構成にはしないでください。来場者端末はフロントエンド/バックエンドだけを見る構成にします。

## 5. バックエンドで必要な変更

現在のコードはOllama形式です。LM Studioへ移行する場合は、次のように変更します。

### 5.1 設定を追加する

`backend/app/core/config.py` に、少なくとも次の設定を追加します。

```python
AI_PROVIDER: str = "ollama"
LMSTUDIO_BASE_URL: str = "http://localhost:1234/v1"
LMSTUDIO_API_KEY: str = "lm-studio"
LMSTUDIO_MODEL: str = "ここにLM Studioの回答モデル名"
LMSTUDIO_EMBEDDING_MODEL: str = "ここにEmbeddingモデル名"
LMSTUDIO_TIMEOUT_SECONDS: float = 300.0
```

`.env` 例:

```env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=ここにLM Studioの回答モデル名
LMSTUDIO_EMBEDDING_MODEL=ここにEmbeddingモデル名
LMSTUDIO_TIMEOUT_SECONDS=300
```

### 5.2 チャットクライアントをOpenAI互換にする

LM Studioのチャットは、OpenAI互換の `POST /v1/chat/completions` を使います。

送信例:

```json
{
  "model": "モデル名",
  "messages": [
    {"role": "system", "content": "あなたは白龍AIガイドです。"},
    {"role": "user", "content": "オカダナルドはどこ？"}
  ],
  "stream": false,
  "temperature": 0.2
}
```

返答の本文は、通常ここに入ります。

```text
choices[0].message.content
```

ストリーミング時は、SSEの `choices[0].delta.content` を順に読む形にします。

### 5.3 EmbeddingクライアントをOpenAI互換にする

LM StudioのEmbeddingは、OpenAI互換の `POST /v1/embeddings` を使います。

送信例:

```json
{
  "model": "Embeddingモデル名",
  "input": "白龍祭の案内テスト"
}
```

Embedding配列は、通常ここに入ります。

```text
data[0].embedding
```

### 5.4 adminのモデル状態確認を直す

現在のadmin画面はOllamaの `/api/tags` 相当を前提にしています。  
LM Studioでは `GET /v1/models` を見て、回答モデルとEmbeddingモデルがロードされているか確認するようにします。

## 6. 本番PCでの移行作業順

本番PCでのおすすめ順:

1. LM Studioをインストールする。
2. 回答用モデルをダウンロード・ロードする。
3. Embedding用モデルをダウンロード・ロードする。
4. LM Studio Local Serverを `http://localhost:1234` で起動する。
5. `curl http://localhost:1234/v1/models` でモデル一覧を確認する。
6. Codexにコード変更を依頼する。
7. `.env` にLM Studio設定を書く。
8. バックエンドを再起動する。
9. `validate_exhibition_data.py --profile production` を実行する。
10. `seed_exhibitions_from_data.py --profile production` を実行する。
11. `ingest_documents.py --profile production` を実行する。
12. `python run.py` で起動する。
13. admin画面で回答モデル・検索モデル・RAG投入がOKになるか確認する。
14. チャットで不明項目を捏造しないか確認する。

## 7. 本番PCのCodexに渡す依頼文

本番PCでCodexを開いたら、次の依頼文を使ってください。

```text
白龍AIガイドを、本番PCのGPU都合でOllamaからLM Studioへ移行したいです。

まず docs/lmstudio_migration_guide.md、docs/production_pc_migration_guide.md、docs/latest_operation_guide.md を読んでください。
現在のコードはOllamaの /api/chat、/api/generate、/api/embeddings 前提なので、LM StudioのOpenAI互換APIに対応させてください。

やってほしいこと:
1. backend/app/core/config.py に AI_PROVIDER、LMSTUDIO_BASE_URL、LMSTUDIO_API_KEY、LMSTUDIO_MODEL、LMSTUDIO_EMBEDDING_MODEL、LMSTUDIO_TIMEOUT_SECONDS を追加する。
2. チャット送信用に OpenAI互換の /v1/chat/completions を呼ぶクライアントを追加または既存クライアントを拡張する。
3. Embedding用に OpenAI互換の /v1/embeddings を呼ぶクライアントを追加または既存クライアントを拡張する。
4. AI_PROVIDER=lmstudio のときはLM Studioを使い、AI_PROVIDER=ollama のときは既存Ollama処理も残す。
5. adminのモデル状態確認も、LM Studioでは /v1/models を見るようにする。
6. .env.example またはドキュメントにLM Studio用設定例を追加する。
7. productionデータ検証、RAG投入、チャット確認まで行う。

注意:
- 本番PCなので、既存のDB、PIN、Firebase設定を上書きする前には確認してください。
- 不明項目をAIが捏造しないルールは維持してください。
- LM Studioのモデル名は、curl http://localhost:1234/v1/models で確認した実名を使ってください。
```

## 8. `.env` の例

本番PCの `backend/.env` またはプロジェクトルートで読み込まれる `.env` に書く例です。  
実際のモデル名は、本番PCのLM Studioで確認したものに置き換えてください。

```env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=your-chat-model-name
LMSTUDIO_EMBEDDING_MODEL=your-embedding-model-name
LMSTUDIO_TIMEOUT_SECONDS=300

DATABASE_URL=sqlite:///./sql_app.db
RAG_DATA_DIR=../docs/data
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=hakuryu_rag
RAG_TOP_K=4
```

## 9. 動作確認用コマンド

### 9.1 LM Studioモデル一覧

```powershell
curl http://localhost:1234/v1/models
```

### 9.2 Chat Completions確認

```powershell
curl http://localhost:1234/v1/chat/completions `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"ここに回答モデル名\",\"messages\":[{\"role\":\"user\",\"content\":\"こんにちは。短く返事して。\"}],\"stream\":false}"
```

### 9.3 Embedding確認

```powershell
curl http://localhost:1234/v1/embeddings `
  -H "Content-Type: application/json" `
  -d "{\"model\":\"ここにEmbeddingモデル名\",\"input\":\"白龍祭の案内テスト\"}"
```

## 10. 白龍AIガイド側の確認質問

移行後に必ず試す質問:

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

期待すること:

- 分かっている情報は答える。
- PTA、ともっちゃ、岩沢精神病棟などの不明項目は、勝手に作らず「資料では確認できません」と言う。
- 回答が遅すぎる場合は、LM Studio側でより軽いモデルに変える。

## 11. よくある詰まり

### `Connection refused`

LM StudioのLocal Serverが起動していません。  
LM StudioでServerをStartしてください。

### `/v1/models` は返るがチャットが失敗する

回答用モデルがロードされていない可能性があります。  
LM Studio上でチャット用モデルをロードしてください。

### Embeddingが失敗する

Embedding対応モデルがロードされていない、またはモデル名が違う可能性があります。  
`/v1/models` の結果から、Embeddingに使うモデル名を確認してください。

### RAG投入ができない

Embeddingが動いていない可能性が高いです。  
まず `curl http://localhost:1234/v1/embeddings` の単体確認を通してください。

### 回答が遅い

LM Studioで次を調整してください。

- 量子化の軽いモデルを選ぶ。
- Context lengthを大きくしすぎない。
- GPU offloadの設定を見直す。
- 同時に重いアプリを動かさない。

## 12. Ollamaに戻す場合

もしLM Studioが安定しない場合は、`.env` を次のように戻せる設計にしておくと安全です。

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

本番直前はトラブル回避が最優先なので、LM Studioで詰まる場合は一時的にOllamaへ戻す判断もありです。
