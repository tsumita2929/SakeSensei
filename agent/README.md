# 🍶 Sake-Sensei (酒先生) - 日本酒推薦エージェント

日本酒の専門知識とユーザーの好みを組み合わせて、最適な日本酒を推薦するAIエージェントです。

## 主な機能

### 7つのツール

1. **search_sake** - 名前、地域、種類、価格帯で日本酒を検索
2. **semantic_search** - 曖昧な表現や自然言語で意味的に類似した日本酒を検索
3. **recommend_sake** - ユーザーの好みに基づいて日本酒を推薦
4. **pairing_recommendation** - 料理の種類や名前から日本酒とのペアリングを提案
5. **get_sake_details** - 特定の日本酒の詳細情報を取得
6. **search_user_preferences** - ユーザーの過去の好みや会話履歴をMemoryから検索
7. **fetch_sake_price** - Web上から最新の日本酒価格を取得（楽天、Amazon）

### 技術スタック

- **Bedrock Knowledge Base + S3 Vectors**: 日本酒データのベクトル検索
- **AgentCore Memory**: ユーザー好みの長期記憶
- **AgentCore Browser**: リアルタイム価格スクレイピング
- **Strands Agents**: エージェントフレームワーク
- **Bedrock Claude Sonnet 4.5**: 対話モデル

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -e .
playwright install chromium
```

### 2. 環境変数の設定

`.env`ファイルは既に作成されています。必要に応じて値を確認してください：

```bash
cat .env
```

### 3. データのアップロード（初回のみ）

日本酒データをS3にアップロードしてKnowledge Baseに同期します：

```bash
# S3にデータをアップロード
aws s3 cp data/sake_data.json s3://sake-sensei-kb-data-<your-aws-account-id>-us-west-2/

# Knowledge Baseのデータソースを同期
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id YEYBYYQ5GL \
  --data-source-id <DATA_SOURCE_ID>
```

## 実行 / デプロイ

### 1. AgentCoreに設定

```bash
agentcore configure -e agent.py
```

メモリや実行ロール、環境変数（`SAKE_AGENT_KB_ID`, `SAKE_AGENT_MEMORY_ID`, `AWS_REGION` など）を対話形式で登録します。

### 2. コンテナをビルドしてデプロイ

```bash
agentcore launch
```

### 3. エージェントを呼び出して確認

```bash
agentcore invoke '{"prompt": "辛口でスッキリした日本酒を教えて"}'
```

ローカルで挙動を確かめたい場合は、`app.run()` を使って`agent.py`を直接実行し、HTTP経由で同じインターフェースにアクセスできます。

## 使用例

### 基本的な検索

```
🙋 あなた: 新潟の淡麗辛口の日本酒を探しています
```

### セマンティック検索

```
🙋 あなた: 華やかで女性向けの日本酒を教えてください
```

### 料理とのペアリング

```
🙋 あなた: 刺身に合う日本酒は？
```

### 価格情報の取得

```
🙋 あなた: 獺祭の価格を教えて
```

### 推薦（過去の好みを考慮）

```
🙋 あなた: おすすめの日本酒を教えて
```

エージェントは自動的に過去の会話履歴や好みをMemoryから取得して、パーソナライズされた推薦を行います。

## プロジェクト構成

```
SakeRecomend/
├── agent.py              # メインエージェント
├── sake_tools.py         # 7つのツール実装
├── data/
│   └── sake_data.json    # 日本酒データベース
├── .env                  # 環境変数
├── .env.example          # 環境変数テンプレート
├── pyproject.toml        # プロジェクト設定
└── README.md             # このファイル
```

## 環境変数

- `AWS_REGION`: AWSリージョン（us-west-2）
- `SAKE_AGENT_KB_ID`: Bedrock Knowledge Base ID
- `SAKE_AGENT_MEMORY_ID`: AgentCore Memory ID
- `SAKE_KB_BUCKET`: S3バケット名
- `SAKE_VECTOR_BUCKET`: S3 Vectorsバケット名
- `SAKE_VECTOR_INDEX`: ベクトルインデックス名

## 注意事項

- AgentCore Browserは2025年9月まで無料で使用できます
- 価格スクレイピング機能はWebサイトの構造変更により動作しない可能性があります
- Memoryは会話ごとに自動的に保存され、長期記憶として活用されます
