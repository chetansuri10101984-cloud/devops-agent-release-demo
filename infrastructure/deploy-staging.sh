#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Deploy Order Service to AWS (Staging)
# 
# This script deploys the clean staging version of the Order Service
# using AWS SAM. It creates:
#   - DynamoDB table (orders)
#   - Lambda function (API handler)
#   - API Gateway (public HTTPS endpoint)
#   - Seed data (15 sample orders)
#
# Prerequisites:
#   - AWS CLI configured with valid credentials
#   - AWS SAM CLI installed (https://docs.aws.amazon.com/sam/)
#
# Usage:
#   ./deploy-staging.sh
# ─────────────────────────────────────────────────────────────

set -e

STACK_NAME="release-workshop-staging"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"
ENVIRONMENT="staging"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Order Service - Staging Deployment                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "  Stack Name:  ${STACK_NAME}"
echo "  Region:      ${REGION}"
echo "  Environment: ${ENVIRONMENT}"
echo ""

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
    exit 1
fi

if ! command -v sam &> /dev/null; then
    echo "❌ AWS SAM CLI not found. Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Verify AWS credentials
echo "🔍 Verifying AWS credentials..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
    echo "❌ AWS credentials not configured. Run: aws configure"
    exit 1
}
echo "   Account: ${ACCOUNT_ID}"
echo ""

# Build
echo "📦 Building Lambda package..."
cd "$(dirname "$0")"
sam build \
    --template-file staging-stack.yaml \
    --region "${REGION}"

echo ""

# Deploy
echo "🚀 Deploying to AWS..."
sam deploy \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset \
    --parameter-overrides "Environment=${ENVIRONMENT}"

echo ""

# Get outputs
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ Deployment Complete!                                  ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "  API URL: ${API_URL}"
echo ""
echo "  Test it:"
echo "    curl ${API_URL}/api/health"
echo ""
echo "  Use this URL as your Test Profile target in Module 4:"
echo "    ${API_URL}"
echo ""
echo "  To delete later:"
echo "    aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${REGION}"
echo ""
