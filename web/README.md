# No Agenda AI Mixer - Web Interface

AWS Lambda-powered web interface for creating AI-generated No Agenda show mixes.

## Features

- **AI Idea Generation**: Uses GROK to generate creative mix concepts
- **Music Generation**: Creates AI music with Fal.ai's Cassette AI
- **Verbose Logging**: Tracks every step of the creative process
- **Session Management**: Save and review all mix creation sessions
- **CloudFront CDN**: Fast global delivery of mixes

## Setup

### 1. Prerequisites

- AWS Account with credentials configured
- Node.js 18+ installed
- Python 3.11 installed
- Serverless Framework CLI

```bash
npm install -g serverless
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
# Edit .env with your keys
```

### 3. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node dependencies
npm install
```

### 4. Deploy to AWS

The deployment script automatically reads API keys from the .env file and stores them securely in AWS Secrets Manager:

```bash
# Deploy (reads from config/.env or .env automatically)
./deploy.sh
```

The script will:
1. Load API keys from your .env file
2. Store them in AWS Secrets Manager
3. Deploy the Lambda function with proper permissions
4. Set up API Gateway and CloudFront

## Local Development

Run the Flask app locally:

```bash
python app.py
```

Visit http://localhost:5000

## API Endpoints

### Start Session
```
POST /api/start_session
{
  "episode_number": 1779,
  "theme": "Best Of"
}
```

### Generate Ideas
```
POST /api/generate_ideas/<session_id>
```

### Generate Music
```
POST /api/generate_music/<session_id>
{
  "prompt": "upbeat electronic intro",
  "duration": 30
}
```

### Create Mix Plan
```
POST /api/create_mix_plan/<session_id>
{
  "selected_segments": []
}
```

### Get Session Data
```
GET /api/session/<session_id>
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  CloudFront │────▶│ API Gateway  │────▶│   Lambda   │
└─────────────┘     └──────────────┘     └────────────┘
                                                 │
                           ┌─────────────────────┼─────────────────────┐
                           │                     │                     │
                     ┌─────▼─────┐        ┌─────▼─────┐        ┌─────▼─────┐
                     │    S3     │        │   GROK    │        │   Fal.ai  │
                     │  Storage  │        │    API    │        │    API    │
                     └───────────┘        └───────────┘        └───────────┘
```

## Session Data Structure

Each session tracks:

- **Ideas**: AI-generated creative concepts
- **Music Generations**: AI-created music tracks
- **Clips**: Audio segments from episodes
- **Mix Plans**: Detailed production plans
- **Logs**: Complete activity timeline
- **Metadata**: Episode info, timestamps, etc.

## Monitoring

View Lambda logs:
```bash
npm run logs
```

View specific session logs:
```bash
aws logs tail /aws/lambda/no-agenda-mixer-dev-app --follow
```

## Cost Optimization

- Lambda: ~$0.0000166667 per GB-second
- API Gateway: $3.50 per million requests
- CloudFront: $0.085 per GB transfer
- S3: $0.023 per GB storage

Estimated monthly cost for moderate usage: $10-20

## Troubleshooting

### Large File Uploads
Lambda has a 6MB payload limit. For larger audio files:
1. Upload directly to S3
2. Pass S3 URL to Lambda

### Cold Starts
First request may take 5-10 seconds. Solutions:
- Enable Lambda provisioned concurrency
- Use Lambda SnapStart
- Implement warming endpoints

### API Rate Limits
- GROK: Check x.ai documentation
- Fal.ai: 100 requests/minute default

## Security

- API keys stored in AWS Secrets Manager
- CloudFront with AWS WAF protection
- Lambda function with minimal IAM permissions
- CORS configured for your domain only