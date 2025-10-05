# Sake Sensei - Terraform Infrastructure

ECS Fargate + Cognito を使用した Streamlit アプリケーションのインフラストラクチャコード。

## 📋 構成

### 作成されるリソース

#### 認証（Cognito）
- **User Pool**: ユーザー認証管理
  - メールアドレスでのサインイン
  - パスワードポリシー: 12文字以上、大小英数字+記号必須
  - メール確認による登録
  - MFA サポート（オプション）
- **User Pool Client**: Streamlit アプリ用クライアント
- **User Pool Domain**: ホストされたUI用ドメイン

#### ネットワーク
- VPC (10.0.0.0/16)
- パブリックサブネット × 2 (ALB 用)
- プライベートサブネット × 2 (ECS Fargate 用)
- Internet Gateway
- NAT Gateway × 2
- Route Tables

#### コンピュート
- ECS Cluster (Fargate)
- ECS Service (desired count: 1)
- ECS Task Definition (1 vCPU, 2GB)
- ECR Repository

#### ロードバランサー
- Application Load Balancer (HTTP)
- Target Group
- Security Groups

#### IAM
- ECS Task Execution Role
- ECS Task Role (Cognito, Bedrock へのアクセス権限)

#### 監視
- CloudWatch Logs (/ecs/sakesensei-dev)
- Container Insights

## 🚀 使用方法

### 初回デプロイ

```bash
# 1. 設定ファイル作成
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars を編集

# 2. Terraform 初期化
terraform init

# 3. プラン確認
terraform plan

# 4. デプロイ
terraform apply
```

### Cognito 情報の確認

```bash
# User Pool ID
terraform output cognito_user_pool_id

# Client ID
terraform output cognito_client_id

# Domain
terraform output cognito_domain

# すべての出力
terraform output
```

## 🔧 カスタマイズ

### リソース設定変更

`terraform.tfvars` で以下を変更可能：

```hcl
# ECS タスクサイズ
ecs_task_cpu    = 1024  # 256, 512, 1024, 2048, 4096
ecs_task_memory = 2048  # 512-30720 (CPU に応じて)

# タスク数
ecs_desired_count = 1

# VPC CIDR
vpc_cidr = "10.0.0.0/16"

# AZ
availability_zones = ["us-west-2a", "us-west-2b"]
```

### Cognito 設定変更

`main.tf` の `aws_cognito_user_pool` リソースで変更可能：

- パスワードポリシー
- MFA 設定 (OPTIONAL, REQUIRED, OFF)
- メール設定
- 属性スキーマ
- アカウント復旧設定

## 💰 コスト見積もり

| リソース | 月額概算 |
|---------|---------|
| ECS Fargate (1 vCPU, 2GB) | $30 |
| ALB | $20 |
| NAT Gateway × 2 | $70 |
| Data Transfer | $10 |
| CloudWatch Logs | $5 |
| Cognito (MAU < 50,000) | $0 |
| **合計** | **$135** |

### コスト削減方法

1. **NAT Gateway を1つに削減**
   ```hcl
   availability_zones = ["us-west-2a"]
   ```
   削減額: $35/月

2. **開発時は ECS タスクを停止**
   ```bash
   aws ecs update-service --desired-count 0 ...
   ```

3. **不要時はインフラを削除**
   ```bash
   terraform destroy
   ```

## 🔐 セキュリティ

### Cognito セキュリティ機能

- ✅ Advanced Security Mode (ENFORCED) - 不正アクセス検知
- ✅ パスワードポリシー強制
- ✅ メール確認必須
- ✅ User Existence Error 防止
- ✅ Token Revocation サポート
- ✅ MFA サポート (OPTIONAL)

### ネットワークセキュリティ

- ECS タスクはプライベートサブネットに配置
- Security Group で必要最小限のアクセスのみ許可
- ALB 経由でのみアクセス可能

### IAM

- Task Execution Role: ECR pull, CloudWatch Logs のみ
- Task Role: 必要な AWS サービスへの最小権限

## 📝 State 管理

デフォルトはローカル State。本番環境では S3 バックエンドを推奨。

`backend.tf` で S3 バックエンドを有効化：

```hcl
terraform {
  backend "s3" {
    bucket         = "sakesensei-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
  }
}
```

## 🛠️ トラブルシューティング

### Cognito Domain 重複エラー

Cognito ドメインは一意である必要があります。エラーが出た場合:

```bash
terraform taint random_id.cognito_domain
terraform apply
```

### ECS タスク起動失敗

```bash
# CloudWatch Logs 確認
aws logs tail /ecs/sakesensei-dev --follow

# タスク停止理由確認
aws ecs describe-tasks --cluster ... --tasks ...
```

## 📚 参考リンク

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS ECS Fargate](https://docs.aws.amazon.com/ecs/latest/developerguide/AWS_Fargate.html)
- [Amazon Cognito](https://docs.aws.amazon.com/cognito/)
