from test_fc.prompt import prompt

from openai import OpenAI
import json 
from dotenv import load_dotenv
import os
load_dotenv()

FC_PAYLOAD_TOOLCALL = "function_calling_toolcall.json"
with open(FC_PAYLOAD_TOOLCALL, "r") as f:
    function_def = json.load(f)

# Wrap the function definition in the correct format
tools = [
    {
        "type": "function",
        "function": function_def
    }
]

# Init OpenAI client
api_key = os.getenv("API_KEY")

client = OpenAI(
    api_key=api_key, 
    base_url=f"{os.getenv('HOST_NAME')}/v1",
)

query = "Nêu các luật về phòng, chống bạo lực gia đình."
print("User query:", query)

response = client.chat.completions.create(
    model="CATI-AI/CMC-Legal-LLM-32B-sft-v2",
    messages=[
        {"role": "system", "content": prompt},
        {"role": "user", "content": query}
    ],
    tools=tools,
    tool_choice={
        "type": "function",
        "function": {"name": "extract_intent_and_query"}
    }
)

print("Argument to function call:", response.choices[0].message.tool_calls[0].function.arguments)