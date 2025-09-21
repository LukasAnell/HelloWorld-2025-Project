# src/app.py (optimized)
import os, json, logging, time, threading, hashlib
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = app.logger

# Config (env overrides)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3:8b")
MAX_RESUME_CHARS = int(os.environ.get("MAX_RESUME_CHARS", "9000"))
NUM_PREDICT = int(os.environ.get("NUM_PREDICT", "280"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "90"))
STREAM = os.environ.get("OLLAMA_STREAM", "false").lower() == "true"
WARM_TIMEOUT = int(os.environ.get("WARM_TIMEOUT", "240"))
WARM_PROMPT = os.environ.get("WARM_PROMPT", "Short warmup.")
session = requests.Session()
log = logging.getLogger("warm")

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://resumereviewer.lukasanell.org,http://localhost:5001,http://localhost:8080,http://127.0.0.1:8080,http://localhost"
).split(",")
CORS(app, resources={r"/analyze": {"origins": ALLOWED_ORIGINS}})


def _poll_generation():
    payload = {
        "model": MODEL_NAME,
        "prompt": WARM_PROMPT,
        "stream": False,
        "options": {"num_predict": 8}
    }
    r = session.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
    return r

def _pull_model():
    r = session.post(f"{OLLAMA_URL}/api/pull", json={"model": MODEL_NAME}, timeout=600, stream=True)
    if r.status_code != 200:
        raise RuntimeError(f"Pull failed: {r.status_code} {r.text[:300]}")
    # Consume stream (progress events) until done
    for line in r.iter_lines():
        if not line:
            continue
        if b'"status":"success"' in line or b'"status":"ready"' in line:
            break

def warm_model():
    log.info("Warming model %s ...", MODEL_NAME)
    start = time.time()
    try:
        # Quick version check (optional)
        try:
            v = session.get(f"{OLLAMA_URL}/api/version", timeout=5)
            v.raise_for_status()
        except Exception as e:
            log.warning("Version check failed: %s", e)

        attempt = 0
        while time.time() - start < WARM_TIMEOUT:
            attempt += 1
            try:
                resp = _poll_generation()
                if resp.status_code == 200:
                    log.info("Warm success in %.1fs (attempt %d)", time.time() - start, attempt)
                    return
                if resp.status_code == 404:
                    # Model missing: pull then retry
                    log.warning("Model 404 (not found). Pulling model %s ...", MODEL_NAME)
                    _pull_model()
                    log.info("Pull complete. Retrying generate.")
                else:
                    log.warning("Warm attempt %d got %s: %s", attempt, resp.status_code, resp.text[:200])
            except requests.RequestException as e:
                log.warning("Warm attempt %d network error: %s", attempt, e)
            time.sleep(3)
        log.error("Warm timed out after %.1fs", time.time() - start)
    except Exception as e:
        log.exception("Warm failed: %s", e)


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

@app.post("/analyze")
def analyze():
    started = time.time()
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    resume_raw = data["text"][:MAX_RESUME_CHARS]
    cache_key = hashlib.sha256(resume_raw.encode("utf-8")).hexdigest()
    cached = cache_get(cache_key)
    if cached:
        return jsonify(cached), 200

    prompt = build_prompt(resume_raw)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": "json",
        "stream": STREAM is True,
        "options": {
            "num_predict": NUM_PREDICT,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "mirostat": 0
        }
    }

    try:
        if STREAM:
            resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, stream=True, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return jsonify({"error": "LLM upstream error", "status": resp.status_code}), 502
            collected = []
            for line in resp.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line.decode("utf-8"))
                    piece = obj.get("response", "")
                    if piece:
                        collected.append(piece)
                    if obj.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
            model_text = "".join(collected)
        else:
            resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                return jsonify({"error": "LLM upstream error", "status": resp.status_code}), 502
            body = resp.json()
            model_text = body.get("response", "")

        if not model_text.strip():
            return jsonify({"error": "Empty model response"}), 502

        # Attempt direct parse; fallback to bracket slice
        try:
            parsed = json.loads(model_text)
        except json.JSONDecodeError:
            s = model_text
            a, b = s.find("{"), s.rfind("}")
            if a != -1 and b != -1 and a < b:
                try:
                    parsed = json.loads(s[a:b+1])
                except Exception:
                    return jsonify({"error": "Invalid JSON from model"}), 502
            else:
                return jsonify({"error": "Invalid JSON from model"}), 502

        # Minimal validation
        if "scores" not in parsed or "comments" not in parsed:
            return jsonify({"error": "Model JSON missing keys"}), 502

        cache_set(cache_key, parsed)
        elapsed = time.time() - started
        log.info("Analyze ok in %.2fs (stream=%s)", elapsed, STREAM)
        return jsonify(parsed), 200

    except requests.exceptions.Timeout:
        return jsonify({"error": "LLM timeout"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Connection error", "detail": str(e)}), 502
    except Exception as e:
        log.exception("Unhandled")
        return jsonify({"error": "Internal error", "detail": str(e)}), 500

# Optional: expose current model/config
@app.get("/model_info")
def model_info():
    return jsonify({
        "model": MODEL_NAME,
        "max_resume_chars": MAX_RESUME_CHARS,
        "num_predict": NUM_PREDICT,
        "stream": STREAM
    })
