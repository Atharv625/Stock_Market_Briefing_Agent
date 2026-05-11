# Deployment Guide

## Local Development
1. Create virtual environment and install packages.
2. Copy `.env.example` to `.env`.
3. Run API:
   - `uvicorn src.api.main:app --reload`
4. Test endpoint:
   - `GET /market-summary`

## AWS Deployment (Serverless Framework)
1. Install Serverless CLI:
   - `npm i -g serverless`
2. Configure AWS credentials and region.
3. Deploy:
   - `serverless deploy`
4. Validate:
   - Open API Gateway endpoint `/health`
   - Confirm Lambda scheduled invocations in CloudWatch logs

## EventBridge Schedule (IST Mapping)
- 8:00 AM IST → `cron(30 2 ? * MON-FRI *)`
- 1:00 PM IST → `cron(30 7 ? * MON-FRI *)`
- 4:00 PM IST → `cron(30 10 ? * MON-FRI *)`
- 8:00 PM IST → `cron(30 14 ? * MON-FRI *)`

## Security and Secrets
- Keep API keys in AWS Secrets Manager and map to Lambda env.
- Restrict IAM permissions to DynamoDB table-level and S3 bucket-level actions.
- Enable KMS encryption for S3 and DynamoDB where required.

## Monitoring
- CloudWatch alarms:
  - Lambda errors > 0
  - Lambda duration p95 > timeout threshold
  - DynamoDB throttles > 0
