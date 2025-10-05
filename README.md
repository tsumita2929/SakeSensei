# 🍶 Sake-Sensei (酒先生)

**AI-Powered Japanese Sake Recommendation System**

Sake-Sensei is an intelligent recommendation platform that helps users discover Japanese sake tailored to their preferences. Built with AWS Bedrock AgentCore, it combines knowledge retrieval, user memory, and real-time web data to provide personalized sake recommendations.

---

## ✨ Features

### 🎯 Personalized Recommendations
- AI-powered suggestions based on user preferences and conversation history
- Long-term memory of taste preferences using AgentCore Memory
- Semantic search for natural language queries like "華やかで女性向けの日本酒"

### 🔍 Smart Search & Discovery
- **Attribute-based search**: Filter by name, region, type (純米, 吟醸, etc.), price range
- **Semantic search**: Find sake using descriptive language and flavor profiles
- **Food pairing**: Get sake recommendations for specific dishes or cuisine types

### 💰 Real-Time Pricing
- Live price fetching from Amazon.co.jp using AgentCore Browser
- Compare prices across different retailers
- Price history and availability tracking

### 🔐 Secure Authentication
- AWS Cognito-based user management
- Email verification and MFA support
- Secure session handling with JWT tokens

### 📊 Tasting Notes & History
- Record your sake tasting experiences
- Build your personal sake journal
- Track favorites and preferences over time

---

## 🏗️ Architecture

```
                           ┌─────────────────┐
                           │   CloudFront    │
                           │     ( CDN )     │
                           └────────┬────────┘
                                    │ HTTPS
                                    ↓
┌─────────────────────────────────────────────────────────────┐
│              Application Load Balancer                      │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web App                        │
│                  (ECS Fargate + Cognito)                    │
└───────────────────┬─────────────────────────────────────────┘
                    │ HTTPS
                    ↓
┌─────────────────────────────────────────────────────────────┐
│              Bedrock AgentCore Runtime                      │
│                  (Strands Agent)                            │
└───────────┬─────────────────┬───────────────────┬───────────┘
            │                 │                   │
            ↓                 ↓                   ↓
    ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
    │  Knowledge    │  │  AgentCore   │  │  AgentCore   │
    │     Base      │  │    Memory    │  │   Browser    │
    │  (S3 + RAG)   │  │ (User Prefs) │  │  (Scraping)  │
    └───────────────┘  └──────────────┘  └──────────────┘
```

### Components

- **Agent** (`agent/`) - Python-based AI agent using Strands framework and AWS Bedrock
- **Streamlit** (`streamlit/`) - User-facing web application with chat interface
- **Infrastructure** (`streamlit/terraform/`) - IaC for CloudFront, ECS, VPC, Cognito, and ALB

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+**
- **AWS Account** with access to:
  - AWS Bedrock (Claude Sonnet 4.5)
  - Bedrock AgentCore
  - Cognito, ECS, S3, ECR
- **Terraform** (for infrastructure deployment)
- **Docker** (for containerization)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Sake-Sensei.git
cd Sake-Sensei
```

### 2. Agent Setup

```bash
cd agent

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and resource IDs

# Upload sake data to S3
aws s3 cp data/sake_data.json s3://your-kb-bucket/

# Sync Knowledge Base
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id YOUR_KB_ID \
  --data-source-id YOUR_DATA_SOURCE_ID

# Deploy agent to AgentCore
agentcore configure -e agent.py
agentcore launch

# Test the agent
agentcore invoke '{"prompt": "辛口でスッキリした日本酒を教えて"}'
```

See [`agent/README.md`](agent/README.md) for detailed agent documentation.

### 3. Streamlit App Setup

```bash
cd ../streamlit

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with AgentCore runtime ARN and Cognito details

# Run locally (development)
streamlit run streamlit_app/app.py
```

### 4. Infrastructure Deployment

```bash
cd streamlit/terraform

# Configure Terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings

# Deploy infrastructure
terraform init
terraform plan
terraform apply

# Get outputs
terraform output cognito_user_pool_id
terraform output alb_dns_name
```

See [`streamlit/terraform/README.md`](streamlit/terraform/README.md) for infrastructure details.

---

## 🛠️ Technology Stack

### Backend
- **AWS Bedrock AgentCore** - Serverless agent runtime
- **Strands Agents** - Agent orchestration framework
- **Claude Sonnet 4.5** - LLM for conversational AI
- **Bedrock Knowledge Base** - Vector search for sake data
- **AgentCore Memory** - Long-term user preference storage
- **AgentCore Browser** - Web scraping for real-time pricing

### Frontend
- **Streamlit** - Interactive web application framework
- **AWS Cognito** - Authentication and user management
- **Python 3.13** - Application runtime

### Infrastructure
- **Amazon CloudFront** - CDN for global content delivery and caching
- **AWS ECS Fargate** - Containerized application hosting
- **Application Load Balancer** - HTTP traffic routing
- **Amazon VPC** - Network isolation
- **Amazon ECR** - Container image registry
- **CloudWatch** - Logging and monitoring
- **Terraform** - Infrastructure as Code

---

## 📖 Usage Examples

### Basic Search
```
🙋 User: 新潟の淡麗辛口の日本酒を探しています
🍶 Sake-Sensei: 新潟県は淡麗辛口の代表的な産地です。以下の銘柄がおすすめです...
```

### Semantic Search
```
🙋 User: 華やかで女性向けの日本酒を教えてください
🍶 Sake-Sensei: 華やかな香りが特徴の吟醸酒をご紹介します...
```

### Food Pairing
```
🙋 User: 刺身に合う日本酒は？
🍶 Sake-Sensei: 刺身には淡麗でキレのある日本酒がよく合います...
```

### Price Lookup
```
🙋 User: 獺祭の価格を教えて
🍶 Sake-Sensei: 獺祭の現在の価格を確認します...
```

---

## 🧪 Development

### Running Tests

**Agent tests:**
```bash
cd agent
source .venv/bin/activate
python -m pytest tests/
```

**Streamlit tests:**
```bash
cd streamlit
pytest tests/
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy streamlit_app/
```

---

## 📊 Project Structure

```
Sake-Sensei/
├── agent/                    # Backend AI agent
│   ├── agent.py             # Main agent orchestration
│   ├── sake_tools.py        # 7 tool implementations
│   ├── data/                # Sake database (JSON files)
│   ├── tests/               # Unit tests
│   ├── .env.example         # Environment template
│   └── README.md            # Agent documentation
│
├── streamlit/               # Frontend web application
│   ├── streamlit_app/
│   │   ├── app.py          # Main Streamlit app
│   │   ├── components/     # Auth & AgentCore client
│   │   └── utils/          # Config, session, UI helpers
│   ├── terraform/          # Infrastructure as Code
│   │   ├── main.tf         # ECS + VPC + Cognito resources
│   │   ├── variables.tf    # Terraform variables
│   │   └── outputs.tf      # Resource outputs
│   ├── .env.example        # Environment template
│   └── README.md           # Streamlit documentation
│
├── CLAUDE.md               # AI assistant guidance
└── README.md               # This file
```

---

## 🔧 Configuration

### Agent Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_REGION` | AWS region for services | `us-west-2` |
| `SAKE_AGENT_KB_ID` | Bedrock Knowledge Base ID | `YEYBYYQ5GL` |
| `SAKE_AGENT_MEMORY_ID` | AgentCore Memory ID | `SakeSenseiMemory-xxx` |
| `SAKE_KB_BUCKET` | S3 bucket for KB data | `sake-sensei-kb-data-xxx` |
| `SAKE_VECTOR_BUCKET` | S3 bucket for vectors | `sake-vectors-xxx` |

### Streamlit Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AGENTCORE_RUNTIME_ARN` | AgentCore runtime ARN | `arn:aws:bedrock-agentcore:...` |
| `COGNITO_USER_POOL_ID` | Cognito User Pool ID | `us-west-2_xxxxx` |
| `COGNITO_CLIENT_ID` | Cognito App Client ID | `xxxxxxxxxxxx` |
| `AWS_REGION` | AWS region | `us-west-2` |

---

## 💰 Cost Estimation

**Monthly costs (approximate):**

| Service | Cost |
|---------|------|
| CloudFront (10GB transfer + requests) | $2 |
| ECS Fargate (1 vCPU, 2GB) | $30 |
| Application Load Balancer | $20 |
| NAT Gateway × 2 | $70 |
| Data Transfer | $10 |
| CloudWatch Logs | $5 |
| Bedrock AgentCore | Variable (pay-per-use) |
| Cognito (< 50k MAU) | Free |
| **Estimated Total** | **~$142/month** |

**Cost optimization tips:**
- Reduce NAT Gateways to 1 for dev environments ($35/month savings)
- Stop ECS tasks when not in use
- Use `terraform destroy` for temporary deployments
- CloudFront free tier includes 1TB data transfer out (first 12 months)
- AgentCore Browser is free until September 2025

---

## 🔒 Security

- ✅ CloudFront with HTTPS-only and custom SSL/TLS certificates
- ✅ AWS Cognito authentication with email verification
- ✅ MFA support (optional)
- ✅ Strong password policy (12+ chars, mixed case, numbers, symbols)
- ✅ JWT token-based session management
- ✅ ECS tasks in private subnets with NAT Gateway
- ✅ Security groups with least-privilege access
- ✅ Environment variables for sensitive configuration
- ✅ No hardcoded credentials in code

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AWS Bedrock** for providing the foundational AI services
- **Anthropic Claude** for the conversational AI model
- **Strands Agents** for the agent framework
- Japanese sake producers and enthusiasts for inspiration

---

## 📧 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Sake-Sensei/issues)
- **Documentation**: See component READMEs ([agent/](agent/README.md), [streamlit/](streamlit/README.md))
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Sake-Sensei/discussions)

---

**Enjoy discovering your perfect sake! 🍶 乾杯！**
