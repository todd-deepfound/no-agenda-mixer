"""
AWS Secrets Manager integration for No Agenda Mixer
"""
import os
import json
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    def __init__(self, region_name='us-east-1'):
        self.region_name = region_name
        self.secrets_client = None
        self._secrets_cache = {}
        
    def _get_client(self):
        """Get or create Secrets Manager client"""
        if not self.secrets_client:
            self.secrets_client = boto3.client(
                'secretsmanager',
                region_name=self.region_name
            )
        return self.secrets_client
    
    def get_secret(self, secret_name):
        """Retrieve secret from AWS Secrets Manager with caching"""
        # Check cache first
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]
        
        try:
            client = self._get_client()
            response = client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret
            if 'SecretString' in response:
                secret = json.loads(response['SecretString'])
            else:
                # Binary secret
                secret = response['SecretBinary']
            
            # Cache the secret
            self._secrets_cache[secret_name] = secret
            logger.info(f"Successfully retrieved secret: {secret_name}")
            
            return secret
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret not found: {secret_name}")
            elif error_code == 'AccessDeniedException':
                logger.error(f"Access denied to secret: {secret_name}")
            else:
                logger.error(f"Error retrieving secret {secret_name}: {error_code}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            raise

def load_secrets_to_env():
    """Load secrets from AWS Secrets Manager into environment variables"""
    # Only load from Secrets Manager if running in Lambda
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        logger.info("Running in Lambda, loading secrets from AWS Secrets Manager")
        
        try:
            sm = SecretsManager()
            secrets = sm.get_secret('no-agenda-mixer/api-keys')
            
            # Set environment variables from secrets
            for key, value in secrets.items():
                os.environ[key] = value
                logger.info(f"Loaded secret: {key}")
                
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            # Don't fail the entire app if secrets can't be loaded
            # Fall back to environment variables
    else:
        logger.info("Not running in Lambda, using local environment variables")