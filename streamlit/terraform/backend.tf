# ============================================================================
# Sake Sensei - Terraform Backend Configuration
# ============================================================================

# Option 1: Local Backend (default - simple for initial setup)
# State files are stored locally in the terraform/ directory
# Uncomment this block if you want to explicitly use local backend

# terraform {
#   backend "local" {
#     path = "terraform.tfstate"
#   }
# }

# Option 2: S3 Backend (recommended for production)
# State files are stored in S3 with DynamoDB locking
# Uncomment and configure this block for team environments

# Prerequisites:
# 1. Create S3 bucket: aws s3 mb s3://sakesensei-terraform-state
# 2. Create DynamoDB table: aws dynamodb create-table \
#    --table-name sakesensei-terraform-locks \
#    --attribute-definitions AttributeName=LockID,AttributeType=S \
#    --key-schema AttributeName=LockID,KeyType=HASH \
#    --billing-mode PAY_PER_REQUEST

# terraform {
#   backend "s3" {
#     bucket         = "sakesensei-terraform-state"
#     key            = "dev/terraform.tfstate"
#     region         = "us-west-2"
#     encrypt        = true
#     dynamodb_table = "sakesensei-terraform-locks"
#   }
# }

# Note: After uncommenting your preferred backend, run:
# terraform init -migrate-state
