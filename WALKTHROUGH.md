# Serverless AI Agent for HR: A Beginner's Walkthrough

## What This Project Does

This project builds an AI-powered HR assistant chatbot that employees can talk to in plain English. Instead of digging through policy documents or emailing HR, an employee can type something like "How many vacation days do I have left?" or "Submit a PTO request for next Friday" and get an instant, accurate answer.

Behind the scenes, an Amazon Bedrock Agent powered by the Nova Pro foundation model listens to the question, figures out what the employee is really asking, picks the right backend function to handle it, and returns a conversational response. The entire system runs serverlessly on AWS -- no servers to manage, no infrastructure to maintain, and the whole tutorial costs under $1 to run.

The assistant supports four HR functions:

- **Check leave balance** -- tells an employee how many PTO, sick, and personal days they have remaining.
- **Submit a leave request** -- files a time-off request and enforces business rules (like denying a request when the balance is zero).
- **Get company policy** -- retrieves HR policy details on topics like remote work, dress code, or expense reimbursement.
- **Get team calendar** -- shows who on a given team is out and when.

All data is mocked for five employees across three teams with five company policies, so you can run and experiment with the whole thing without connecting to any real HR system.

---

## Why This Pattern Matters

Most AI chatbot demos stop at "send a prompt, get text back." That is interesting but not useful for real work. Real work requires the AI to **do things**: look up data, enforce rules, update records.

This project demonstrates the **agent pattern** -- the AI model does not just generate text, it acts as a decision-maker that routes requests to the correct backend function, extracts the right parameters from the conversation, and synthesizes the results into a human-friendly answer. This is the bridge between a language model and a production application.

The serverless architecture means you pay only for what you use. There are no idle servers burning money overnight. For an HR assistant that might handle a few hundred queries a day, this keeps costs near zero.

---

## Tech Stack

| Component | Service / Tool | Role |
|---|---|---|
| Foundation Model | Amazon Nova Pro (via Bedrock) | Understands natural language, decides which function to call |
| Agent Orchestration | Amazon Bedrock Agents | Manages conversation flow, function routing, session memory |
| Backend Logic | AWS Lambda (Python) | Executes the four HR functions against mock data |
| Permissions | AWS IAM | Trust policies and permissions for Lambda and Bedrock |
| SDK | boto3 (>= 1.35.0) | Python SDK for interacting with AWS services |
| Language | Python 3.x | All code is Python |

---

## Project Files Explained

| File | Purpose |
|---|---|
| `lambda_function.py` | The Lambda function. Contains all four HR functions, mock data for 5 employees, and a dispatcher that routes incoming requests to the correct function. |
| `invoke_agent.py` | A test script you run locally. Sends five natural-language scenarios to the deployed agent, including a multi-turn conversation, and prints the responses. |
| `function-schema.json` | Defines the four actions the agent can take. Tells the agent what parameters each function expects and what each function does. |
| `lambda-trust-policy.json` | IAM trust policy that allows the Lambda service to assume the execution role. |
| `agent-trust-policy.json` | IAM trust policy that allows the Bedrock service to assume the agent role. |
| `invoke-model-policy.json` | IAM policy that grants permission to invoke foundation models in Bedrock. |
| `requirements.txt` | Python dependency file. Lists `boto3>=1.35.0`. |

---

## File-by-File Breakdown

### lambda_function.py

This is the heart of the project. It has three main sections:

**1. Mock Data**

Five employees are defined as dictionaries with names, employee IDs, teams, and leave balances (PTO, sick days, personal days). Three teams (Engineering, Marketing, Sales) have calendar entries showing who is out and when. Five company policies cover topics like remote work and expense reimbursement.

**2. Four HR Functions**

Each function takes parameters extracted by the agent and returns structured data:

- `check_leave_balance(employee_id)` -- looks up the employee and returns their remaining days for each leave type.
- `submit_leave_request(employee_id, leave_type, start_date, end_date)` -- checks that the employee has enough balance, deducts the days, and returns a confirmation or denial with a reason.
- `get_company_policy(policy_topic)` -- searches the policy list by topic keyword and returns the matching policy text.
- `get_team_calendar(team_name, month)` -- returns scheduled absences for a given team in a given month.

**3. Dispatcher (the Lambda handler)**

The `lambda_handler` function is the entry point that AWS Lambda calls. It receives the event from the Bedrock Agent, reads which action and parameters the agent chose, calls the matching function, and returns the result in the format the agent expects. This is the **dispatcher pattern** -- one Lambda, one handler, routing to many functions based on the action name.

### invoke_agent.py

This script is your testing tool. It uses boto3 to send natural language prompts to the deployed Bedrock Agent and print the responses. It runs five test scenarios:

1. Checking a leave balance ("How many vacation days does Sarah have?")
2. Submitting a PTO request ("Submit a 3-day PTO request for John starting March 10")
3. Looking up a policy ("What is the company's remote work policy?")
4. Checking the team calendar ("Who is out on the Engineering team in March?")
5. Multi-turn conversation -- asks a balance question, then follows up with a leave request in the same session, demonstrating that the agent remembers context across turns.

The script uses a single `session_id` for the multi-turn scenario so the agent maintains conversation state.

### function-schema.json

This JSON file is the contract between the Bedrock Agent and the Lambda function. It defines four action groups, each with:

- A **name** matching the function name in the Lambda code.
- A **description** the agent reads to decide when to use this function.
- **Parameters** with names, types, descriptions, and whether they are required.

The agent uses these descriptions at runtime. When an employee asks "How many sick days do I have?", the agent reads through the schema descriptions, determines that `check_leave_balance` is the best match, extracts the `employee_id` parameter from context, and calls the Lambda with that action and parameter.

### Trust and Permission Policies

- **lambda-trust-policy.json** -- Tells IAM: "The AWS Lambda service is allowed to assume this role." Without this, Lambda cannot run your code.
- **agent-trust-policy.json** -- Tells IAM: "The Amazon Bedrock service is allowed to assume this role." Without this, the agent cannot operate.
- **invoke-model-policy.json** -- Grants the agent's role permission to call `bedrock:InvokeModel` on foundation models. Without this, the agent cannot talk to Nova Pro.

### requirements.txt

Contains a single line: `boto3>=1.35.0`. This version or later is required because Bedrock Agents support was added in later boto3 releases.

---

## Key Concepts

### Bedrock Agent

An Amazon Bedrock Agent is a managed service that wraps a foundation model with the ability to take actions. You give it a model (Nova Pro), a set of functions it can call (the action group), and instructions. It handles the loop of: understand the user's intent, decide which function to call, extract parameters, call the function, and turn the result into a conversational response.

### Action Group

An action group is a collection of functions that an agent can invoke. In this project, the single action group contains all four HR functions. The agent selects from this group based on the user's question.

### Function Schema

The function schema (defined in `function-schema.json`) tells the agent what each function does, what parameters it needs, and what types those parameters are. The agent reads these descriptions like a human would read an API manual -- it uses them to match user intent to the right function.

### AWS Lambda

Lambda is AWS's serverless compute service. You upload your code, and AWS runs it on demand. You do not provision servers. You pay only for the milliseconds your code runs. In this project, a single Lambda function handles all four HR operations through the dispatcher pattern.

### IAM Roles and Trust Policies

IAM (Identity and Access Management) controls who can do what in AWS. A **role** is a set of permissions that a service can assume. A **trust policy** says which service is allowed to assume that role. This project needs two roles:

1. A role for Lambda (trusted by the Lambda service, with permissions to execute and log).
2. A role for the Bedrock Agent (trusted by the Bedrock service, with permissions to invoke foundation models and call the Lambda function).

### Serverless

Serverless means you do not manage any servers. Both the Bedrock Agent and the Lambda function are fully managed by AWS. You deploy code and configuration; AWS handles scaling, patching, and availability. You pay per request, not per hour.

### Session Memory

The Bedrock Agent supports multi-turn conversations by maintaining session state. When you send messages with the same `session_id`, the agent remembers what was said earlier in the conversation. This lets an employee ask "What's my leave balance?" and then follow up with "OK, submit a PTO request for 3 days" without repeating their employee ID.

### Dispatcher Pattern

Instead of deploying four separate Lambda functions (one per HR action), this project uses a single Lambda with a dispatcher. The handler function reads the action name from the incoming event and routes it to the correct internal function. This keeps deployment simple and reduces the number of AWS resources to manage.

---

## How the Agent Decides Which Function to Call

This is the core intelligence of the system. Here is the decision flow:

1. The user sends a natural language message (e.g., "Can I take Friday off?").
2. The Bedrock Agent passes the message to the Nova Pro model along with the function schema descriptions.
3. Nova Pro reads the descriptions of all four functions and determines which one matches the user's intent. In this case, it matches `submit_leave_request`.
4. Nova Pro extracts the required parameters from the conversation. If the employee ID is not in the current message but was mentioned earlier in the session, it pulls it from session memory.
5. If a required parameter is missing and cannot be inferred, the agent asks the user for it ("Which employee ID should I use?").
6. The agent invokes the Lambda function with the chosen action name and extracted parameters.
7. The Lambda dispatcher routes to the correct internal function, executes it, and returns structured data.
8. The agent takes the structured data and generates a natural, conversational response for the user.

The agent never sees raw code or database queries. It only sees function descriptions and parameters. The quality of those descriptions in the function schema directly affects how well the agent routes requests.

---

## Data Flow

```
Employee                Bedrock Agent              Lambda Function
   |                        |                           |
   |  "How many PTO days    |                           |
   |   does Sarah have?"    |                           |
   |----------------------->|                           |
   |                        |                           |
   |                   [Nova Pro reads                  |
   |                    function schemas,               |
   |                    selects check_leave_balance,    |
   |                    extracts employee_id=E001]      |
   |                        |                           |
   |                        |  Invoke Lambda with       |
   |                        |  action: check_leave_balance
   |                        |  employee_id: E001        |
   |                        |-------------------------->|
   |                        |                           |
   |                        |              [Dispatcher routes to
   |                        |               check_leave_balance(),
   |                        |               looks up E001 in
   |                        |               mock data, returns
   |                        |               {PTO: 12, Sick: 5,
   |                        |                Personal: 3}]
   |                        |                           |
   |                        |  Structured result        |
   |                        |<--------------------------|
   |                        |                           |
   |                   [Nova Pro converts               |
   |                    structured data into            |
   |                    conversational response]        |
   |                        |                           |
   |  "Sarah has 12 PTO     |                           |
   |   days, 5 sick days,   |                           |
   |   and 3 personal days  |                           |
   |   remaining."          |                           |
   |<-----------------------|                           |
```

---

## How to Run It Yourself

These are the high-level steps using the AWS CLI. You need an AWS account with Bedrock access enabled in your region.

### Step 1: Clone the Repository

```bash
git clone https://github.com/sachinm207/serverless-bedrock-agent.git
cd serverless-bedrock-agent
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Create the Lambda Execution Role

```bash
aws iam create-role \
  --role-name hr-agent-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

aws iam attach-role-policy \
  --role-name hr-agent-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

### Step 4: Package and Deploy the Lambda Function

```bash
zip lambda_function.zip lambda_function.py

aws lambda create-function \
  --function-name hr-agent-function \
  --runtime python3.12 \
  --role arn:aws:iam::<YOUR_ACCOUNT_ID>:role/hr-agent-lambda-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 30
```

### Step 5: Create the Bedrock Agent Role

```bash
aws iam create-role \
  --role-name hr-bedrock-agent-role \
  --assume-role-policy-document file://agent-trust-policy.json

aws iam put-role-policy \
  --role-name hr-bedrock-agent-role \
  --policy-name invoke-model-policy \
  --policy-document file://invoke-model-policy.json
```

### Step 6: Add Lambda Invoke Permission to the Agent Role

```bash
aws iam put-role-policy \
  --role-name hr-bedrock-agent-role \
  --policy-name invoke-lambda-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:<REGION>:<ACCOUNT_ID>:function:hr-agent-function"
    }]
  }'
```

### Step 7: Create the Bedrock Agent

```bash
aws bedrock-agent create-agent \
  --agent-name hr-assistant-agent \
  --agent-resource-role-arn arn:aws:iam::<ACCOUNT_ID>:role/hr-bedrock-agent-role \
  --foundation-model "amazon.nova-pro-v1:0" \
  --instruction "You are an HR assistant. Help employees check leave balances, submit leave requests, look up company policies, and view team calendars."
```

### Step 8: Create the Action Group

Use the agent ID returned from Step 7 to create an action group with the function schema:

```bash
aws bedrock-agent create-agent-action-group \
  --agent-id <AGENT_ID> \
  --agent-version DRAFT \
  --action-group-name hr-functions \
  --action-group-executor lambdaArn=arn:aws:lambda:<REGION>:<ACCOUNT_ID>:function:hr-agent-function \
  --function-schema file://function-schema.json
```

### Step 9: Allow Bedrock to Invoke the Lambda

```bash
aws lambda add-permission \
  --function-name hr-agent-function \
  --statement-id allow-bedrock-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com
```

### Step 10: Prepare and Create an Alias

```bash
aws bedrock-agent prepare-agent --agent-id <AGENT_ID>

aws bedrock-agent create-agent-alias \
  --agent-id <AGENT_ID> \
  --agent-alias-name hr-agent-live
```

### Step 11: Run the Test Script

Update `invoke_agent.py` with your agent ID and alias ID, then run:

```bash
python invoke_agent.py
```

You should see conversational responses for all five test scenarios, including the multi-turn conversation where the agent remembers context from the first message.

---

## Glossary

| Term | Definition |
|---|---|
| Amazon Bedrock | AWS managed service for accessing foundation models (large language models) via API. |
| Bedrock Agent | A Bedrock feature that gives a foundation model the ability to call external functions and maintain conversation state. |
| Foundation Model | A large pre-trained AI model. This project uses Amazon Nova Pro. |
| Nova Pro | Amazon's own foundation model available through Bedrock, used here for understanding HR questions. |
| Action Group | A set of functions that a Bedrock Agent is allowed to call. Defined by a function schema. |
| Function Schema | A JSON document describing each function's name, purpose, and parameters so the agent knows when and how to use it. |
| AWS Lambda | Serverless compute service. Runs your code on demand without managing servers. |
| Lambda Handler | The entry-point function that AWS Lambda calls when the function is triggered. |
| Dispatcher Pattern | A design where one handler routes requests to different internal functions based on an action name. |
| IAM | Identity and Access Management. AWS service for controlling permissions. |
| IAM Role | A set of permissions that an AWS service can assume to perform actions. |
| Trust Policy | A JSON document that specifies which AWS service is allowed to assume an IAM role. |
| Session ID | A unique identifier for a conversation. Messages with the same session ID share memory, enabling multi-turn conversations. |
| Multi-turn Conversation | A conversation where the AI remembers previous messages, so the user does not need to repeat context. |
| Serverless | An architecture where the cloud provider manages all infrastructure. You pay only for actual usage. |
| boto3 | The official AWS SDK for Python. Used to interact with AWS services programmatically. |
| Mock Data | Fake, hardcoded data used for testing and demonstration purposes instead of connecting to a real database. |

---

**Source Code:** [github.com/sachinm207/serverless-bedrock-agent](https://github.com/sachinm207/serverless-bedrock-agent)
**Blog Post:** [dev.to/sachinm207 -- How to Build a Serverless AI Agent with Amazon Bedrock and Lambda](https://dev.to/sachinm207/how-to-build-a-serverless-ai-agent-with-amazon-bedrock-and-lambda-6l1)
