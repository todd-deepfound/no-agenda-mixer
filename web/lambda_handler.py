"""
AWS Lambda handler for No Agenda Mixer Flask app
"""
from mangum import Mangum
from app import app

# Create the handler for AWS Lambda
handler = Mangum(app)