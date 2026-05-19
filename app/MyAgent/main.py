# from strands import Agent, tool
# from bedrock_agentcore.runtime import BedrockAgentCoreApp
# from model.load import load_model
# import requests

# app = BedrockAgentCoreApp()
# log = app.logger

# @tool
# def fetch_w3schools(topic: str) -> str:
#     """
#     Fetch W3Schools Python documentation for a given topic.
#     Topic examples: for_loops, while_loops, functions, classes,
#     dictionaries, lists, tuples, sets, lambda, inheritance,
#     iterators, scope, modules, datetime, math, json, regex
#     """
#     topic = topic.lower().strip().replace(" ", "_")
#     url = f"https://www.w3schools.com/python/python_{topic}.asp"
#     try:
#         response = requests.get(url, timeout=10)
#         if response.status_code == 200:
#             return response.text[:3000]
#         url2 = f"https://www.w3schools.com/python/{topic}.asp"
#         response2 = requests.get(url2, timeout=10)
#         if response2.status_code == 200:
#             return response2.text[:3000]
#         return f"W3Schools: topic '{topic}' not found. Try: for_loops, while_loops, functions, classes, dictionaries, lists"
#     except Exception as e:
#         return f"W3Schools error: {str(e)}"

# @tool
# def fetch_python_docs(topic: str) -> str:
#     """Fetch official Python documentation for a given topic."""
#     url = f"https://docs.python.org/3/search.html?q={topic}"
#     try:
#         return requests.get(url, timeout=10).text[:3000]
#     except Exception as e:
#         return f"Python docs error: {str(e)}"

# _agent = None

# def get_or_create_agent():
#     global _agent
#     if _agent is None:
#         _agent = Agent(
#             model=load_model(),
#             system_prompt="You are a helpful assistant. Use tools when appropriate.",
#             tools=[fetch_w3schools, fetch_python_docs]
#         )
#     return _agent

# @app.entrypoint
# async def invoke(payload, context):
#     log.info("Invoking Agent.....")
#     agent = get_or_create_agent()
#     stream = agent.stream_async(payload.get("prompt"))
#     async for event in stream:
#         if "data" in event and isinstance(event["data"], str):
#             yield event["data"]

# if __name__ == "__main__":
#     app.run()




from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
import requests
import boto3
import json

app = BedrockAgentCoreApp()
log = app.logger

@tool
def fetch_w3schools(topic: str) -> str:
    """
    Fetch W3Schools Python documentation for a given topic.
    Topic examples: for_loops, while_loops, functions, classes,
    dictionaries, lists, tuples, sets, lambda, inheritance,
    iterators, scope, modules, datetime, math, json, regex
    """
    topic = topic.lower().strip().replace(" ", "_")
    url = f"https://www.w3schools.com/python/python_{topic}.asp"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.text[:3000]
        url2 = f"https://www.w3schools.com/python/{topic}.asp"
        response2 = requests.get(url2, timeout=10)
        if response2.status_code == 200:
            return response2.text[:3000]
        return f"W3Schools: topic '{topic}' not found. Try: for_loops, while_loops, functions, classes, dictionaries, lists"
    except Exception as e:
        return f"W3Schools error: {str(e)}"

@tool
def fetch_python_docs(topic: str) -> str:
    """Fetch official Python documentation for a given topic."""
    url = f"https://docs.python.org/3/search.html?q={topic}"
    try:
        return requests.get(url, timeout=10).text[:3000]
    except Exception as e:
        return f"Python docs error: {str(e)}"

@tool
def vault_get_secret(secret_path: str) -> str:
    """
    Retrieve a secret from HashiCorp Vault before accessing any AWS resource.
    Always call this first to fetch credentials or config before doing S3 operations.
    secret_path: path to the secret e.g. 'kv/vtiger_crm', 'kv/myagent_config'
    """
    try:
        import hvac
        import os
        vault_password = os.environ.get("VAULT_PASSWORD")
        if not vault_password:
            return "Vault error: VAULT_PASSWORD environment variable not set"
        client = hvac.Client(url="http://10.59.39.79:8200")
        client.auth.userpass.login(
            username="varadrajan.kunsavalikar",
            password=vault_password
        )
        if not client.is_authenticated():
            return "Vault authentication failed"
        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=secret_path,
                mount_point="secrets"
            )
            data = response.get("data", {}).get("data", {})
            keys = list(data.keys())
            return f"Successfully retrieved secret from Vault path '{secret_path}'. Keys found: {keys}"
        except Exception:
            response = client.secrets.kv.v1.read_secret(
                path=secret_path,
                mount_point="secrets"
            )
            data = response.get("data", {})
            keys = list(data.keys())
            return f"Successfully retrieved secret from Vault path '{secret_path}'. Keys found: {keys}"
    except Exception as e:
        return f"Vault error: {str(e)}"

@tool
def s3_read(key: str) -> str:
    """
    Read a file from the authmind-agentcore-telemetry S3 bucket.
    Use this to retrieve stored notes, results, or any previously saved content.
    key: the filename to read e.g. 'notes.txt', 'summary.json'
    """
    try:
        s3 = boto3.client("s3", region_name="ap-south-1")
        response = s3.get_object(
            Bucket="authmind-agentcore-telemetry",
            Key=key
        )
        return response["Body"].read().decode("utf-8")
    except Exception as e:
        return f"S3 read error: {str(e)}"

@tool
def s3_write(key: str, content: str) -> str:
    """
    Write content to the authmind-agentcore-telemetry S3 bucket.
    Use this to save summaries, results, or notes for later retrieval.
    key: filename to save as e.g. 'notes.txt', 'summary.json'
    content: the text content to save
    """
    try:
        s3 = boto3.client("s3", region_name="ap-south-1")
        s3.put_object(
            Bucket="authmind-agentcore-telemetry",
            Key=key,
            Body=content.encode("utf-8")
        )
        return f"Successfully saved '{key}' to S3 bucket."
    except Exception as e:
        return f"S3 write error: {str(e)}"

_agent = None

def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt="You are a helpful assistant. Use tools when appropriate.",
            tools=[fetch_w3schools, fetch_python_docs, vault_get_secret, s3_read, s3_write]
        )
    return _agent

@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")
    agent = get_or_create_agent()
    stream = agent.stream_async(payload.get("prompt"))
    async for event in stream:
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]

if __name__ == "__main__":
    app.run()