import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

def request_ollama(path, json=None, timeout=30):
    """
    Example helper to call Ollama service inside Docker network.
    Usage: request_ollama('/v1/generate', json={...})
    Adjust 'path' to the correct Ollama HTTP API endpoint you need.
    """
    url = OLLAMA_URL.rstrip('/') + path
    resp = requests.post(url, json=json or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
