#!/bin/bash

# Deploy No Agenda Mixer to AWS Lambda

echo "🚀 Deploying No Agenda Mixer to AWS Lambda..."

# Load environment variables from .env if it exists
if [ -f "../config/.env" ]; then
    export $(grep -v '^#' ../config/.env | xargs)
elif [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Setup secrets in AWS Secrets Manager
echo "🔐 Setting up AWS Secrets Manager..."
python setup_secrets.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to setup secrets"
    exit 1
fi

# Install npm dependencies
echo "📦 Installing npm dependencies..."
npm install

# Deploy to AWS
echo "☁️ Deploying to AWS Lambda..."
npx serverless deploy --verbose

# Get the endpoint URL
echo "✅ Deployment complete!"
echo ""
echo "📌 Your API endpoints:"
npx serverless info --verbose | grep -E "endpoint|ANY"

echo ""
echo "🌐 CloudFront Distribution:"
npx serverless info --verbose | grep -E "CloudFrontDistribution"

echo ""
echo "📊 View logs with:"
echo "   npm run logs"

echo ""
echo "🗑️ To remove deployment:"
echo "   npm run remove"