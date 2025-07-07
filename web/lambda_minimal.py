"""
AWS Lambda handler for minimal Flask app
"""
from mangum import Mangum
from app_minimal import app

# Create the handler for AWS Lambda
handler = Mangum(app)