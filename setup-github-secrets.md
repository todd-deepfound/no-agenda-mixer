# 🔑 GitHub Secrets Setup for No Agenda Mixer

## Required Secrets

Before pushing to GitHub, you need to add these secrets to your repository:

### 1. AWS Credentials
Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- **`AWS_ACCESS_KEY_ID`**: Your AWS access key
- **`AWS_SECRET_ACCESS_KEY`**: Your AWS secret key

### 2. API Keys
- **`GROK_API_KEY`**: Your x.ai GROK API key
- **`FAL_API_KEY`**: Your FAL.ai API key

## How to Add Secrets

1. Go to: https://github.com/toddllm/no-agenda-mixer/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret one by one

## Optional: OIDC Setup (More Secure)

Instead of storing AWS credentials, you can use OIDC:

### Create OIDC Provider in AWS
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### Create IAM Role for GitHub Actions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::717984198385:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:toddllm/no-agenda-mixer:*"
        }
      }
    }
  ]
}
```

Then uncomment the OIDC sections in `.github/workflows/deploy.yml` and comment out the secrets sections.

## Quick Start (Using Secrets)

For fastest setup, just add the 4 secrets above and push your code!