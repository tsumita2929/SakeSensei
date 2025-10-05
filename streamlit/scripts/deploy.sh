#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${PROJECT_ROOT}/streamlit_app/VERSION"
AWS_REGION="us-west-2"
ECS_CLUSTER="sakesensei-cluster-dev"
ECS_SERVICE="sakesensei-service-dev"
APP_DIR="${PROJECT_ROOT}/streamlit_app"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Sake Sensei Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get ECR repository URL from Terraform
echo -e "${BLUE}Getting ECR repository URL...${NC}"
cd "${PROJECT_ROOT}/terraform"
ECR_REPO=$(terraform output -raw ecr_repository_url 2>/dev/null)
if [ -z "$ECR_REPO" ]; then
    echo -e "${RED}Error: Could not get ECR repository URL from Terraform${NC}"
    exit 1
fi
cd "${PROJECT_ROOT}"

# Read current version
CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')
echo -e "${BLUE}Current version: ${CURRENT_VERSION}${NC}"

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Determine version bump type (default: patch)
BUMP_TYPE="${1:-patch}"

case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo -e "${RED}Error: Invalid bump type. Use: major, minor, or patch${NC}"
        echo -e "${YELLOW}Usage: $0 [major|minor|patch]${NC}"
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
VERSION_TAG="v${NEW_VERSION}"

echo -e "${GREEN}New version: ${NEW_VERSION} (${VERSION_TAG})${NC}"
echo ""

# Confirm deployment
read -p "Deploy version ${VERSION_TAG}? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Step 1/5: Logging in to Amazon ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REPO}

echo ""
echo -e "${BLUE}Step 2/5: Building Docker image...${NC}"
docker build \
    --platform linux/amd64 \
    -t ${ECR_REPO}:${VERSION_TAG} \
    -t ${ECR_REPO}:latest \
    ${APP_DIR}

echo ""
echo -e "${BLUE}Step 3/5: Pushing Docker image to ECR...${NC}"
echo -e "  Pushing ${VERSION_TAG}..."
docker push ${ECR_REPO}:${VERSION_TAG}
echo -e "  Pushing latest..."
docker push ${ECR_REPO}:latest

echo ""
echo -e "${BLUE}Step 4/5: Updating VERSION file...${NC}"
echo "${NEW_VERSION}" > "${VERSION_FILE}"
echo -e "${GREEN}  VERSION file updated to ${NEW_VERSION}${NC}"

echo ""
echo -e "${BLUE}Step 5/5: Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER} \
    --service ${ECS_SERVICE} \
    --force-new-deployment \
    --region ${AWS_REGION} \
    --no-cli-pager > /dev/null

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Deployment Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Deployment Details:${NC}"
echo -e "  Version: ${VERSION_TAG}"
echo -e "  ECR Image: ${ECR_REPO}:${VERSION_TAG}"
echo -e "  ECS Cluster: ${ECS_CLUSTER}"
echo -e "  ECS Service: ${ECS_SERVICE}"
echo ""
echo -e "${YELLOW}Monitor deployment status:${NC}"
echo -e "  ${BLUE}aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${ECS_SERVICE} --region ${AWS_REGION}${NC}"
echo ""
echo -e "${YELLOW}View application logs:${NC}"
echo -e "  ${BLUE}aws logs tail /ecs/sakesensei-dev --follow --region ${AWS_REGION}${NC}"
echo ""
echo -e "${YELLOW}Access application:${NC}"
cd "${PROJECT_ROOT}/terraform"
ALB_URL=$(terraform output -raw alb_url 2>/dev/null)
if [ -n "$ALB_URL" ]; then
    echo -e "  ${BLUE}${ALB_URL}${NC}"
fi
echo ""
