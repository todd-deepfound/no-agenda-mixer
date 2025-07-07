#!/usr/bin/env python3
"""
Lightweight Health Check for No Agenda Mixer Production System
Provides basic health monitoring without heavy dependencies
"""

import json
import os
from datetime import datetime

def lambda_handler(event, context):
    """Lightweight health check Lambda handler"""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': ''
            }
        
        # Basic health check
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'system_type': os.environ.get('SYSTEM_TYPE', 'production'),
            'stage': os.environ.get('STAGE', 'dev'),
            'lambda_context': {
                'function_name': context.function_name if context else 'unknown',
                'memory_limit': context.memory_limit_in_mb if context else 'unknown',
                'remaining_time': context.get_remaining_time_in_millis() if context else 'unknown'
            },
            'environment': {
                's3_bucket': os.environ.get('S3_BUCKET', 'not_configured'),
                'log_level': os.environ.get('LOG_LEVEL', 'INFO')
            },
            'version': '1.0.0',
            'message': 'No Agenda Mixer Production System is operational'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(health_status, indent=2)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'system_type': os.environ.get('SYSTEM_TYPE', 'production')
            })
        }

if __name__ == '__main__':
    # For local testing
    test_event = {'httpMethod': 'GET'}
    
    class MockContext:
        function_name = 'health-check-local'
        memory_limit_in_mb = 256
        def get_remaining_time_in_millis(self):
            return 30000
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(json.loads(result['body']), indent=2))