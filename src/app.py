# src/app.py
import os
import json
import logging

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = app.logger

# CORS: allow the production domain and common local dev origins
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "https://resumereviewer.lukasanell.org,http://localhost:5001,http://localhost:8080,http://127.0.0.1:8080,http://localhost"
).split(",")
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=False)

# Get the Ollama service URL from an environment variable, with a default for local testing
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3")


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": "Method Not Allowed"}), 405


@app.errorhandler(500)
def handle_500(e):
    logger.exception("Unhandled server error: %s", e)
    # Do not leak internals in production; include message for debugging
    return jsonify({"error": "Internal Server Error", "detail": str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """
    Receives resume text from the frontend, sends it to Ollama for analysis,
    and returns the analysis to the frontend.
    """
    data = request.get_json(silent=True)
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    resume_text = data['text']

    # The prompt for Ollama
    prompt = f"""
    You are a resume reviewer. Analyze the following resume text and respond ONLY with a single valid JSON object matching this exact schema. Do not include backticks, markdown, comments, or any text outside the JSON. Use integers 0-5 for all scores and clamp values within range.

    Required JSON schema:
    {{
      "scores": [
        {{"name": "Content / Relevance", "score": 0, "max": 5}},
        {{"name": "Achievements / Results", "score": 0, "max": 5}},
        {{"name": "Skills / Keywords", "score": 0, "max": 5}},
        {{"name": "Organization / Formatting", "score": 0, "max": 5}},
        {{"name": "Professionalism", "score": 0, "max": 5}}
      ],
      "comments": ["string", "string", "..."]
    }}

    Notes:
    - "comments" should be specific, actionable bullet points (1 sentence each). Include 6-15 bullets.
    - Keep category names exactly as shown above.
    - Explain your reasoning only via the comments list.

    Resume Text:
    ---
    {resume_text}
    ---

    Rubric (guidance only):
    Resume Rubric with 5 categories (0-5 each, total 25):
    Content/Relevance; Achievements/Results; Skills/Keywords; Organization/Formatting; Professionalism.
    Use the following level descriptions when assigning scores:

    score of 0: Missing key sections; only duties; no skills; unreadable; unprofessional tone.
    score of 1: Mostly irrelevant/generic; no contributions; vague skills; inconsistent formatting; many errors.
    score of 2: Some relevant roles; general achievements; skills not tied to experiences; cluttered; uneven tone.
    score of 3: Somewhat related experiences; half show contributions; >=5 relevant skills; clear structure; few errors.
    score of 4: Well-chosen relevant experiences; mostly specific outcomes; balanced skills tied to experiences; professional look; mostly error-free.
    score of 5: Fully tailored; clear measurable impact; highly relevant skills; polished and consistent; error-free.
    """

    # Truncate very large resumes to avoid long tokenize time
    MAX_CHARS = 12000  # adjust as needed
    resume_text = resume_text[:MAX_CHARS]

    ollama_payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": "json",
        "stream": True  # set True if you want incremental output & faster first byte
    }

    try:
        # Forward the request to the Ollama container (with timeout)
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=ollama_payload, timeout=120)
        try:
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.exceptions.HTTPError as http_err:
            body = None
            try:
                body = response.text
            except Exception:
                body = None
            logger.warning("Ollama HTTP error: %s; status=%s; body_snippet=%s", http_err, getattr(response, 'status_code', None), (body or '')[:500])
            return jsonify({
                "error": "Upstream LLM error",
                "status": getattr(response, 'status_code', None),
                "body": (body or '')[:1000]
            }), 502

        # Ollama returns the model output as a string in the 'response' key (which should itself be JSON)
        analysis_result = response.json()
        raw = analysis_result.get('response', '')
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except Exception as je:
            logger.warning("Model returned invalid JSON: %s; raw_snippet=%s", je, str(raw)[:500])
            return jsonify({"error": "Model returned invalid JSON", "detail": str(je), "raw": raw}), 502
        return jsonify(parsed), 200

    except requests.exceptions.RequestException as e:
        logger.error("Could not connect to Ollama service: %s", e)
        return jsonify({"error": f"Could not connect to Ollama service: {e}"}), 502
    except Exception as e:
        logger.exception("Unexpected error during analysis: %s", e)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# Compatibility routes for proxies that strip path prefixes (e.g., handle_path)
@app.route('/', methods=['GET'])
def health_compat():
    return health()

@app.route('/', methods=['POST'])
def analyze_compat():
    return analyze_resume()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
