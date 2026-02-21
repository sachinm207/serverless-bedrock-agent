import boto3
import uuid
import os

client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

# Replace with your agent ID, or set the BEDROCK_AGENT_ID env var
AGENT_ID = os.environ.get("BEDROCK_AGENT_ID", "YOUR_AGENT_ID")
AGENT_ALIAS_ID = "TSTALIASID"  # built-in test alias

def invoke(prompt, session_id=None):
    if not session_id:
        session_id = str(uuid.uuid4())

    print(f"\n{'='*60}")
    print(f"User: {prompt}")
    print(f"Session: {session_id[:8]}...")
    print(f"{'='*60}")

    resp = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=prompt,
    )

    answer = ""
    for event in resp["completion"]:
        if "chunk" in event:
            answer += event["chunk"]["bytes"].decode("utf-8")

    print(f"\nAgent: {answer}")
    return session_id, answer


if __name__ == "__main__":
    print("=" * 60)
    print("HR Leave Agent — Live Tests")
    print("=" * 60)

    # Test 1: Check leave balance
    print("\n>>> TEST 1: Check leave balance")
    sid, _ = invoke("How many PTO days does employee EMP001 have left?")

    # Test 2: Company policy lookup
    print("\n>>> TEST 2: Policy lookup")
    invoke("What's the remote work policy?")

    # Test 3: Team calendar
    print("\n>>> TEST 3: Team calendar")
    invoke("Who on the engineering team is out in March?")

    # Test 4: Submit a leave request
    print("\n>>> TEST 4: Submit leave request")
    invoke("Submit a PTO request for EMP003 from March 20 to March 24, 2026.")

    # Test 5: Multi-turn — check balance then request
    print("\n>>> TEST 5: Multi-turn conversation")
    sid, _ = invoke("I'm employee EMP004. How much PTO do I have?")
    invoke("Can I take March 10 off as PTO?", session_id=sid)

    print("\n" + "=" * 60)
    print("All tests complete.")
