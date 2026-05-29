# 本番PCのCodexに渡すプロンプト

以下をそのまま本番PCのCodexに貼ってください。

```text
白龍AIガイドを、本番PCのGPU都合でOllamaからLM Studioへ移行したいです。

まず docs/lmstudio_migration_guide.md、docs/production_pc_migration_guide.md、docs/latest_operation_guide.md を読んで、現在の構成を把握してください。

現在のコードはOllamaの /api/chat、/api/generate、/api/embeddings 前提です。
LM StudioはOpenAI互換APIとして http://localhost:1234/v1 を使う想定です。

やってほしいこと:
1. LM Studio Local Server が起動しているか確認する。
2. curl http://localhost:1234/v1/models でロード済みモデル名を確認する。
3. backend/app/core/config.py に LM Studio用設定を追加する。
   - AI_PROVIDER
   - LMSTUDIO_BASE_URL
   - LMSTUDIO_API_KEY
   - LMSTUDIO_MODEL
   - LMSTUDIO_EMBEDDING_MODEL
   - LMSTUDIO_TIMEOUT_SECONDS
4. AI_PROVIDER=lmstudio のとき、チャットは /v1/chat/completions を使うようにする。
5. AI_PROVIDER=lmstudio のとき、Embeddingは /v1/embeddings を使うようにする。
6. AI_PROVIDER=ollama の既存処理は消さず、戻せるようにする。
7. admin画面のモデル状態確認も、LM Studio時は /v1/models を見るようにする。
8. .env.example またはドキュメントにLM Studio用の設定例を追加する。
9. productionデータ検証を実行する。
10. RAG投入を実行する。
11. python run.py で起動し、ブラウザでチャット・admin・待ち時間を確認する。

注意:
- 本番PCなので、既存DB、スタッフPIN、Firebase設定を上書きする前には確認してください。
- 不明項目をAIが捏造しないプロンプト方針は維持してください。
- モデル名は推測せず、/v1/models で出た名前を使ってください。
- Embeddingが失敗する場合は、LM StudioでEmbedding対応モデルをロードしてからやり直してください。
```

## LM Studio用 `.env` 例

```env
AI_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_API_KEY=lm-studio
LMSTUDIO_MODEL=your-chat-model-name
LMSTUDIO_EMBEDDING_MODEL=your-embedding-model-name
LMSTUDIO_TIMEOUT_SECONDS=300
```
