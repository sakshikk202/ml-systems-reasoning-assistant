import os
from openai import OpenAI


def hf_chat(prompt: str, system: str = "You are a helpful assistant.") -> str:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not set")

    model = os.environ.get("HF_MODEL")
    if not model:
        raise RuntimeError("HF_MODEL not set")

    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=token,
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=700,
    )

    content = resp.choices[0].message.content
    return content if content else ""