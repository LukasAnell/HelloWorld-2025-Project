# src/app.py (optimized)
import os, json, logging, time, threading, hashlib
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = app.logger

# Config (env overrides)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3:8b")
MAX_RESUME_CHARS = int(os.environ.get("MAX_RESUME_CHARS", "6000"))
NUM_PREDICT = int(os.environ.get("NUM_PREDICT", "170"))
REQUEST_CONNECT_TIMEOUT = int(os.getenv("REQUEST_CONNECT_TIMEOUT", "5"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
REQUEST_READ_TIMEOUT = int(os.getenv("REQUEST_READ_TIMEOUT", "240"))
STREAM = os.environ.get("OLLAMA_STREAM", "false").lower() == "true"
CACHE_SIZE = int(os.environ.get("CACHE_SIZE", "64"))
WARM_TIMEOUT = int(os.environ.get("WARM_TIMEOUT", "240"))
WARM_PROMPT = os.environ.get("WARM_PROMPT", "Short warmup.")
session = requests.Session()
log = logging.getLogger("warm")

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://resumereviewer.lukasanell.org,http://localhost:5001,http://localhost:8080,http://127.0.0.1:8080,http://localhost"
).split(",")
CORS(app, resources={r"/analyze": {"origins": ALLOWED_ORIGINS}})

# Simple in‑memory LRU-ish cache (bounded)
_CACHE = {}
_CACHE_MAX = 32

def cache_get(key):
    item = _CACHE.get(key)
    if item:
        item["ts"] = time.time()
        return item["value"]
    return None

def cache_set(key, value):
    if len(_CACHE) >= _CACHE_MAX:
        # Evict oldest
        oldest = min(_CACHE.items(), key=lambda kv: kv[1]["ts"])[0]
        _CACHE.pop(oldest, None)
    _CACHE[key] = {"value": value, "ts": time.time()}

RUBRIC_ORDER = [
    "Content / Relevance",
    "Achievements / Results",
    "Skills / Keywords",
    "Organization / Formatting",
    "Professionalism"
]

BASE_PROMPT_TEMPLATE = """You are a strict resume reviewer.
Return ONLY compact JSON (no markdown) with:
{{
  "scores":[
    {scores_schema}
  ],
  "comments":[ "short actionable bullet", "..."]
}}
Rules:
- scores are integers 0-5.
- keep names EXACT.
- 6-12 concise improvement bullets.
Resume:
---
{resume}
---
"""

def build_scores_schema():
    return ",".join(
        [f'{{"name":"{n}","score":0,"max":5}}' for n in RUBRIC_ORDER]
    )

def build_prompt(resume_text):
    return BASE_PROMPT_TEMPLATE.format(
        scores_schema=build_scores_schema(),
        resume=resume_text
    )

def warm_model():
    try:
        log.info("Warming model %s ...", MODEL_NAME)
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": "Return JSON: {\"ok\":true}",
                "format": "json",
                "stream": False,
                "options": {"num_predict": 12}
            },
            timeout=60
        )
        log.info("Warm status %s", r.status_code)
    except Exception as e:
        log.warning("Warm failed: %s", e)

threading.Thread(target=warm_model, daemon=True).start()

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

def warm_model():
    try:
        log.info("Warming model %s", MODEL_NAME)
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": "ping", "stream": False, "options": {"num_predict": 1}},
            timeout=(REQUEST_CONNECT_TIMEOUT, 30)
        )
        if r.ok:
            log.info("Model warm completed")
        else:
            log.warning("Warm model non-200: %s %s", r.status_code, r.text[:120])
    except Exception as e:
        log.warning("Warm model failed: %s", e)

@app.before_first_request
def _init():
    # Fire and forget warm-up
    try:
        warm_model()
    except Exception:
        pass

def _ollama_payload(prompt, stream=False, num_predict=None):
    return {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": "json",
        "stream": stream,
        "options": {
            "num_predict": num_predict if num_predict is not None else NUM_PREDICT
        }
    }

def _call_ollama(payload, stream: bool):
    # Use tuple timeout: (connect, read)
    return requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        stream=stream,
        timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT)
    )

def _stream_response(resp):
    # Ollama streaming: each line is a JSON object; final one has "done": true
    def gen():
        partial = ""
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            # Pass through raw lines or accumulate into merged JSON if desired
            yield line + "\n"
    return Response(stream_with_context(gen()), mimetype="application/jsonl")

@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Truncate to reduce tokenization delay
    text = text[:12000]

    prompt = f"""You are a resume reviewer. Return ONLY valid JSON (no markdown). Schema:
    {{
     "scores":[
      {{"name":"Content / Relevance","score":0,"max":5}},
      {{"name":"Achievements / Results","score":0,"max":5}},
      {{"name":"Skills / Keywords","score":0,"max":5}},
      {{"name":"Organization / Formatting","score":0,"max":5}},
      {{"name":"Professionalism","score":0,"max":5}}
     ],
     "comments":["string","string"]
    }}
    Rules: 6-15 concise actionable comments; integer scores 0-5.

    Resume:
    ---
    {text}
    ---"""

    want_stream = ENABLE_STREAM or request.args.get("stream") == "1"

    try:
        payload = _ollama_payload(prompt, stream=want_stream)
        if want_stream:
            resp = _call_ollama(payload, stream=True)
            resp.raise_for_status()
            # Stream JSONL to client; client can parse incrementally
            return _stream_response(resp)

        # Non-stream (single JSON string in 'response')
        resp = _call_ollama(payload, stream=False)
        resp.raise_for_status()
        outer = resp.json()
        raw = outer.get("response", "")
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except Exception as je:
            logger.warning("Invalid model JSON: %s snippet=%s", je, str(raw)[:400])
            return jsonify({"error": "Model returned invalid JSON", "raw": raw}), 502
        return jsonify(parsed), 200
    except requests.HTTPError as he:
        body = he.response.text[:800] if he.response is not None else ""
        return jsonify(
            {"error": "Upstream LLM error", "status": getattr(he.response, "status_code", None), "body": body}), 502
    except requests.RequestException as re:
        return jsonify({"error": f"Ollama request failed: {re}"}), 502
    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({"error": "Internal failure", "detail": str(e)}), 500

# Optional: expose current model/config
@app.get("/model_info")
def model_info():
    return jsonify({
        "model": MODEL_NAME,
        "max_resume_chars": MAX_RESUME_CHARS,
        "num_predict": NUM_PREDICT,
        "stream": STREAM
    })
