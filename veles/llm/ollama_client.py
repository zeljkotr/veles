"""
veles/llm/ollama_client.py

Centralized Ollama client - single source of truth for the model name
and endpoint URL. Both brain.py and reporter.py previously duplicated
this configuration separately, risking drift if one got updated and
the other didn't. Now both import from here instead.
"""

import json
import re

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3:8b"


def call_ollama(prompt: str, temperature: float = 0.2, num_predict: int = 200) -> str:
    """Sends a prompt to the local Ollama model and returns the raw response text."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        },
        timeout=(10, 600),
    )
    response.raise_for_status()
    return response.json()["response"]


def extract_json(text: str):
    """
    Pulls the first {...} block out of a model response and parses it.
    Models sometimes add stray text around JSON despite instructions not
    to - this keeps callers from having to handle that themselves.
    Returns None if no valid JSON object is found.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None