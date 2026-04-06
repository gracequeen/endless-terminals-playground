
from aicore_llm_access import get_anthropic_completion

messages = [
    {"role": "user", "content": "hi"}
]

response = get_anthropic_completion(
    messages=messages,
    model="claude_4"
)

print(response)