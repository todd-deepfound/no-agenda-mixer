#!/bin/bash

# Deploy Professional No Agenda Mixer
# This script sets up the complete professional audio processing system

set -e

echo "🎧 Deploying No Agenda Professional AI Mixer"
echo "=============================================="

# Check dependencies
echo "📋 Checking dependencies..."

# Check if serverless is installed
if ! command -v serverless &> /dev/null; then
    echo "❌ Serverless Framework not found. Installing..."
    npm install -g serverless
fi

# Check if required plugins are available
echo "📦 Installing serverless plugins..."
npm install --save-dev serverless-python-requirements serverless-plugin-warmup

# Install professional audio libraries
echo "🔊 Installing professional audio processing libraries..."
pip install -r requirements_professional.txt

# Set up AWS secrets if they don't exist
echo "🔐 Setting up AWS secrets..."
python3 << EOF
import boto3
import json
import os
from pathlib import Path

def setup_secrets():
    try:
        secrets_client = boto3.client('secretsmanager')
        
        # Load API keys from config
        config_path = Path('../config/.env')
        secrets = {}
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        secrets[key] = value
        
        if secrets:
            try:
                # Try to update existing secret
                secrets_client.update_secret(
                    SecretId='no-agenda-mixer/api-keys',
                    SecretString=json.dumps(secrets)
                )
                print("✅ Updated existing AWS secrets")
            except secrets_client.exceptions.ResourceNotFoundException:
                # Create new secret
                secrets_client.create_secret(
                    Name='no-agenda-mixer/api-keys',
                    SecretString=json.dumps(secrets),
                    Description='API keys for No Agenda Professional Mixer'
                )
                print("✅ Created new AWS secrets")
        else:
            print("⚠️  No API keys found in config/.env")
            
    except Exception as e:
        print(f"⚠️  Could not set up secrets: {e}")

setup_secrets()
EOF

# Deploy the professional mixer
echo "🚀 Deploying professional mixer to AWS Lambda..."

# First deploy with container image support for heavy libraries
echo "📦 Building deployment package..."

# Deploy professional system
serverless deploy -c serverless-professional.yml --verbose

# Get the deployment information
echo "✅ Deployment complete!"

# Test the deployment
echo "🧪 Testing professional system..."
python3 << EOF
import requests
import json

def test_professional_system():
    try:
        # Get the API URL from serverless output
        # In practice, you'd parse this from the deployment output
        api_url = "https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/dev"
        
        # Test health endpoint
        print("Testing professional system health...")
        health_response = requests.get(f"{api_url}/health", timeout=30)
        
        if health_response.status_code == 200:
            print("✅ Professional system is healthy")
            health_data = health_response.json()
            print(f"   GROK API: {'✅' if health_data.get('has_grok_key') else '❌'}")
            print(f"   FAL.ai API: {'✅' if health_data.get('has_fal_key') else '❌'}")
        else:
            print(f"⚠️  Health check failed: {health_response.status_code}")
            
    except Exception as e:
        print(f"⚠️  Test failed: {e}")
        print("Note: Run manual tests after deployment URLs are available")

test_professional_system()
EOF

echo ""
echo "🎉 Professional No Agenda Mixer Deployment Complete!"
echo "======================================================"
echo ""
echo "📁 Files created:"
echo "   • professional_mixer.py - Advanced audio processing engine"
echo "   • professional_frontend.html - Enhanced UI with professional features"
echo "   • serverless-professional.yml - Optimized Lambda configuration"
echo "   • requirements_professional.txt - Professional audio libraries"
echo ""
echo "🌐 Access your professional mixer:"
echo "   • Open professional_frontend.html in your browser"
echo "   • Use the professional mixing controls"
echo "   • Generate high-quality audio mixes with AI"
echo ""
echo "🎛️  Professional Features Available:"
echo "   ✅ Advanced EQ, Compression, Reverb processing"
echo "   ✅ Intelligent audio segmentation with Librosa"
echo "   ✅ Professional crossfading and mastering"
echo "   ✅ AI music generation with FAL.ai"
echo "   ✅ High-quality 24-bit audio output"
echo "   ✅ Theme-based processing chains"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update API URLs in professional_frontend.html"
echo "   2. Test with different themes and episodes"
echo "   3. Monitor CloudWatch logs for performance"
echo "   4. Scale memory/timeout based on usage"
echo ""
echo "📊 Monitoring:"
echo "   • CloudWatch Logs: /aws/lambda/no-agenda-mixer-pro-dev-professional-mixer"
echo "   • S3 Bucket: no-agenda-mixer-audio-dev"
echo "   • CloudFront Distribution: Available in AWS Console"
echo ""