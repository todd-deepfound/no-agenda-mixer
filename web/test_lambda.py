"""
Test Lambda locally
"""
import os
os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'test'
os.environ['GROK_API_KEY'] = 'test'
os.environ['FAL_API_KEY'] = 'test'

from lambda_handler import handler

# Test event
event = {
    "httpMethod": "GET",
    "path": "/",
    "headers": {},
    "body": None
}

context = {}

result = handler(event, context)
print(result)