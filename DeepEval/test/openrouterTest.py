import requests
import json
import time

# Testing the openrouter model connection

HEADERS = {
  "Authorization": "Bearer <OpenRouter_API_Key>",
  "Content-Type": "application/json",
}

MODEL = "nvidia/nemotron-3.5-lightning:free"


def call_openrouter(payload, max_retries=5):
    for attempt in range(max_retries):
        resp = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            data=json.dumps(payload),
        ).json()

        if 'choices' in resp:
            return resp

        error = resp.get('error', {})
        if error.get('code') in (429, 503) and attempt < max_retries - 1:
            wait = error.get('metadata', {}).get('retry_after_seconds', 5)
            print(f"Rate limited/unavailable, retrying in {wait}s... ({attempt + 1}/{max_retries})")
            time.sleep(wait)
            continue

        raise RuntimeError(f"OpenRouter error: {resp}")


# First API call with reasoning
response = call_openrouter({
    "model": MODEL,
    "messages": [
        {
          "role": "user",
          "content": "How many r's are in the word 'strawberry'?"
        }
      ],
    "reasoning": {"enabled": True}
})

# Extract the assistant message with reasoning_details
message = response['choices'][0]['message']

# Preserve the assistant message with reasoning_details
messages = [
  {"role": "user", "content": "How many r's are in the word 'strawberry'?"},
  {
    "role": "assistant",
    "content": message.get('content'),
    "reasoning_details": message.get('reasoning_details')  # Pass back unmodified
  },
  {"role": "user", "content": "Are you sure? Think carefully."}
]

# Second API call - model continues reasoning from where it left off
response2 = call_openrouter({
    "model": MODEL,
    "messages": messages,  # Includes preserved reasoning_details
    "reasoning": {"enabled": True}
})

print(response2['choices'][0]['message'].get('content'))
