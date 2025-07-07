#!/usr/bin/env python3
"""
Test AWS Secrets Manager retrieval
"""
from secrets_manager import SecretsManager
import json

def test_secrets():
    """Test retrieving secrets from AWS Secrets Manager"""
    print("🔐 Testing AWS Secrets Manager retrieval...\n")
    
    try:
        sm = SecretsManager()
        secrets = sm.get_secret('no-agenda-mixer/api-keys')
        
        print("✅ Successfully retrieved secrets!")
        print("\n📋 Secret keys found:")
        for key in secrets.keys():
            # Don't print the actual values
            print(f"   - {key}: {'*' * 10}")
        
        # Verify expected keys
        expected_keys = ['GROK_API_KEY', 'FAL_API_KEY', 'GROK_API_URL', 'GROK_MODEL']
        missing_keys = [k for k in expected_keys if k not in secrets]
        
        if missing_keys:
            print(f"\n⚠️ Missing keys: {missing_keys}")
        else:
            print("\n✅ All expected keys are present!")
            
    except Exception as e:
        print(f"❌ Error retrieving secrets: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_secrets()