#!/usr/bin/env python3
"""
Setup AWS Secrets Manager with API keys for No Agenda Mixer
"""
import os
import json
import boto3
from dotenv import load_dotenv
import sys

def create_or_update_secret(client, secret_name, secret_data, region='us-east-1'):
    """Create or update a secret in AWS Secrets Manager"""
    try:
        # Try to create the secret
        response = client.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret_data),
            Description='API keys for No Agenda Mixer'
        )
        print(f"✅ Created secret: {secret_name}")
        return response['ARN']
    except client.exceptions.ResourceExistsException:
        # Secret exists, update it
        response = client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secret_data)
        )
        print(f"✅ Updated secret: {secret_name}")
        return response['ARN']
    except Exception as e:
        print(f"❌ Error with secret {secret_name}: {e}")
        return None

def main():
    """Setup all required secrets"""
    print("🔐 Setting up AWS Secrets Manager for No Agenda Mixer\n")
    
    # Load environment variables
    env_path = '../config/.env'
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv('.env')
    
    # Get API keys
    grok_api_key = os.getenv('GROK_API_KEY')
    fal_api_key = os.getenv('FAL_API_KEY')
    
    if not grok_api_key or not fal_api_key:
        print("❌ Error: Missing API keys")
        print("Make sure GROK_API_KEY and FAL_API_KEY are set in .env")
        sys.exit(1)
    
    # Initialize AWS client
    try:
        session = boto3.Session()
        region = session.region_name or 'us-east-1'
        secrets_client = boto3.client('secretsmanager', region_name=region)
        print(f"📍 Using AWS region: {region}\n")
    except Exception as e:
        print(f"❌ Error initializing AWS client: {e}")
        print("Make sure you have AWS credentials configured")
        sys.exit(1)
    
    # Create secrets
    secrets = {
        'no-agenda-mixer/api-keys': {
            'GROK_API_KEY': grok_api_key,
            'FAL_API_KEY': fal_api_key,
            'GROK_API_URL': os.getenv('GROK_API_URL', 'https://api.x.ai/v1'),
            'GROK_MODEL': os.getenv('GROK_MODEL', 'grok-3-latest')
        }
    }
    
    arns = []
    for secret_name, secret_data in secrets.items():
        arn = create_or_update_secret(secrets_client, secret_name, secret_data, region)
        if arn:
            arns.append(arn)
    
    print("\n📋 Summary:")
    print(f"✅ Successfully configured {len(arns)} secret(s)")
    
    if arns:
        print("\n🔗 Secret ARNs:")
        for arn in arns:
            print(f"   {arn}")
    
    print("\n📝 Next steps:")
    print("1. Update serverless.yml to grant Lambda access to these secrets")
    print("2. Deploy with: ./deploy.sh")
    print("\n✨ Secrets are ready for use!")

if __name__ == "__main__":
    main()