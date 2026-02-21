# Serverless AI Agent with Bedrock + Lambda

An HR assistant agent built on Amazon Bedrock Agents and AWS Lambda. The agent handles leave balance lookups, time-off requests, company policy questions, and team calendar checks — all through natural language.

Companion code for the blog post: [How to Build a Serverless AI Agent with Amazon Bedrock and Lambda](#)

## Project Structure

```
├── lambda_function.py        # Lambda function — HR backend with 4 actions
├── invoke_agent.py           # Test script — invoke the agent with sample queries
├── function-schema.json      # Action group function definitions
├── lambda-trust-policy.json  # IAM trust policy for Lambda execution role
├── agent-trust-policy.json   # IAM trust policy for Bedrock Agent role
├── invoke-model-policy.json  # IAM policy allowing bedrock:InvokeModel
└── requirements.txt
```

## Prerequisites

- AWS account with Bedrock access (us-east-1)
- AWS CLI v2 configured
- Python 3.12+
- Amazon Nova Pro model access enabled

## Quick Start

1. Replace `YOUR_ACCOUNT_ID` in `agent-trust-policy.json` with your 12-digit AWS account ID.

2. Create IAM roles:

```bash
aws iam create-role --role-name hr-leave-agent-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

aws iam attach-role-policy --role-name hr-leave-agent-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam create-role --role-name hr-leave-agent-bedrock-role \
  --assume-role-policy-document file://agent-trust-policy.json

aws iam put-role-policy --role-name hr-leave-agent-bedrock-role \
  --policy-name BedrockInvokeModelPolicy \
  --policy-document file://invoke-model-policy.json
```

3. Deploy the Lambda function:

```bash
zip lambda_function.zip lambda_function.py

aws lambda create-function --function-name hr-leave-agent \
  --runtime python3.12 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/hr-leave-agent-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 30 --memory-size 128

aws lambda add-permission --function-name hr-leave-agent \
  --statement-id AllowBedrockInvoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-account YOUR_ACCOUNT_ID
```

4. Create the Bedrock Agent and action group (see blog post for full CLI commands and the agent instruction prompt).

5. Test:

```bash
export BEDROCK_AGENT_ID=your-agent-id
pip install boto3
python invoke_agent.py
```

## What the Agent Can Do

| Function | Example Query |
|----------|--------------|
| Check leave balance | "How many PTO days does EMP001 have?" |
| Submit time off | "Submit PTO for EMP003 from March 20-24" |
| Policy lookup | "What's the remote work policy?" |
| Team calendar | "Who on engineering is out in March?" |

## Cleanup

```bash
aws bedrock-agent delete-agent --agent-id YOUR_AGENT_ID
aws lambda delete-function --function-name hr-leave-agent
aws iam delete-role-policy --role-name hr-leave-agent-bedrock-role --policy-name BedrockInvokeModelPolicy
aws iam delete-role --role-name hr-leave-agent-bedrock-role
aws iam detach-role-policy --role-name hr-leave-agent-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name hr-leave-agent-lambda-role
```
