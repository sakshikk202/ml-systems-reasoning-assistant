# llm.py
import os
from openai import OpenAI

DEFAULT_SYSTEM_PROMPT = "You are an ML systems reliability expert. Be concise and actionable."

def hf_chat(prompt: str, system: str = DEFAULT_SYSTEM_PROMPT) -> str:
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not set")

    model = os.getenv("HF_MODEL", "HuggingFaceH4/zephyr-7b-beta")

    client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=token,
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        return f"LLM error: {str(e)}"