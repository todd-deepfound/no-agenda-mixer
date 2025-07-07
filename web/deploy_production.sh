#!/bin/bash
# Deploy Production Script for No Agenda Professional Mixer
# Builds container image and deploys to AWS Lambda

set -e

echo "🚀 Deploying No Agenda Professional Mixer to Production"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi
print_status "Docker available"

# Check Serverless Framework
if ! command -v serverless &> /dev/null; then
    print_error "Serverless Framework is not installed"
    echo "Install with: npm install -g serverless"
    exit 1
fi
print_status "Serverless Framework available"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed"
    exit 1
fi
print_status "AWS CLI available"

# Get AWS account info
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    print_error "Failed to get AWS account ID. Check AWS credentials."
    exit 1
fi
AWS_REGION=${AWS_REGION:-us-east-1}

print_info "AWS Account: $AWS_ACCOUNT_ID"
print_info "AWS Region: $AWS_REGION"

# ECR repository
ECR_REPO="noagenda-mixer-production"
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO"

# Step 1: Create ECR repository if it doesn't exist
echo ""
echo "📦 Setting up ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPO --region $AWS_REGION 2>/dev/null; then
    print_status "ECR repository already exists"
else
    print_info "Creating ECR repository..."
    aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
    print_status "ECR repository created"
fi

# Step 2: Build Docker image
echo ""
echo "🐳 Building Docker container image..."
docker build -t $ECR_REPO:latest -f Dockerfile .
if [ $? -eq 0 ]; then
    print_status "Docker image built successfully"
else
    print_error "Docker build failed"
    exit 1
fi

# Step 3: Tag and push to ECR
echo ""
echo "📤 Pushing image to ECR..."

# Get ECR login token
print_info "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

# Tag image
docker tag $ECR_REPO:latest $ECR_URI:latest
docker tag $ECR_REPO:latest $ECR_URI:prod

# Push to ECR
docker push $ECR_URI:latest
docker push $ECR_URI:prod

print_status "Image pushed to ECR"

# Step 4: Deploy with Serverless
echo ""
echo "⚡ Deploying with Serverless Framework..."

# Check if API keys are set
if [ -z "$GROK_API_KEY" ] || [ -z "$FAL_API_KEY" ]; then
    print_warning "GROK_API_KEY or FAL_API_KEY not set in environment"
    print_info "Set them with: export GROK_API_KEY=your_key FAL_API_KEY=your_key"
fi

# Deploy
serverless deploy --config serverless-production.yml --stage prod

if [ $? -eq 0 ]; then
    print_status "Deployment successful!"
else
    print_error "Deployment failed"
    exit 1
fi

# Step 5: Get deployment info
echo ""
echo "📊 Deployment Information"
echo "========================"

# Get API endpoint
API_ENDPOINT=$(serverless info --config serverless-production.yml --stage prod | grep "endpoint:" | head -1 | awk '{print $2}')

if [ -n "$API_ENDPOINT" ]; then
    echo "API Endpoint: $API_ENDPOINT"
    echo ""
    echo "🧪 Test Commands:"
    echo "Health Check:"
    echo "  curl $API_ENDPOINT/health"
    echo ""
    echo "Mixer Health:"
    echo "  curl $API_ENDPOINT/mix/health"
    echo ""
    echo "Create Mix:"
    echo "  curl -X POST $API_ENDPOINT/mix/professional \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"episode_url\": \"https://op3.dev/e/mp3s.nashownotes.com/NA-1779-2025-07-06-Final.mp3\", \"theme\": \"Best Of\", \"target_duration\": 90}'"
    echo ""
    echo "Metrics:"
    echo "  curl $API_ENDPOINT/metrics"
else
    print_warning "Could not retrieve API endpoint"
fi

echo ""
echo "📝 Next Steps:"
echo "1. Run production smoke tests: python3 production_test.py $API_ENDPOINT"
echo "2. Monitor CloudWatch logs"
echo "3. Check S3 bucket: noagenda-mixer-prod"
echo "4. View metrics in CloudWatch dashboard"

echo ""
print_status "Production deployment complete! 🎉"