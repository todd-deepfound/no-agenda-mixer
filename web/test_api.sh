#!/bin/bash

API_URL="https://x0wr03bhe8.execute-api.us-east-1.amazonaws.com/dev"

echo "🔍 Testing No Agenda Mixer API..."
echo ""

# Test root endpoint
echo "1. Testing GET /"
curl -X GET "$API_URL/" -H "Content-Type: application/json"
echo -e "\n"

# Test starting a session
echo "2. Testing POST /api/start_session"
curl -X POST "$API_URL/api/start_session" \
  -H "Content-Type: application/json" \
  -d '{"episode_number": 1779, "theme": "Test Theme"}' 
echo -e "\n"

echo "✅ Tests complete"