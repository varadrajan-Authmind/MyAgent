from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
import requests

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

_agent = None

def get_or_create_agent():
    global _agent
    if _agent is None:
        _agent = Agent(
            model=load_model(),
            system_prompt="You are a helpful assistant. Use tools when appropriate.",
            tools=[fetch_w3schools, fetch_python_docs]
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
