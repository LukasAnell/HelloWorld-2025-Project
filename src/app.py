# src/app.py
import os
import json

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

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


@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """
    Receives resume text from the frontend, sends it to Ollama for analysis,
    and returns the analysis to the frontend.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    resume_text = data['text']

    # The prompt for Ollama
    prompt = f"""
    You are a resume reviewer. Analyze the following resume text and respond ONLY with a single valid JSON object matching this exact schema. Do not include backticks, markdown, comments, or any text outside the JSON. Use integers 0-5 for all scores and clamp values within range.

    Required JSON schema:
    {
      "scores": [
        {"name": "Content / Relevance", "score": 0, "max": 5},
        {"name": "Achievements / Results", "score": 0, "max": 5},
        {"name": "Skills / Keywords", "score": 0, "max": 5},
        {"name": "Organization / Formatting", "score": 0, "max": 5},
        {"name": "Professionalism", "score": 0, "max": 5}
      ],
      "comments": ["string", "string", "..."]
    }

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

    try:
        # The payload to send to Ollama's API
        ollama_payload = {
            "model": MODEL_NAME,  # Configurable via env
            "prompt": prompt,
            "format": "json",  # Request JSON output from Ollama
            "stream": False
        }

        # Forward the request to the Ollama container
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=ollama_payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Ollama returns the model output as a string in the 'response' key (which should itself be JSON)
        analysis_result = response.json()
        raw = analysis_result.get('response', '')
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except Exception as je:
            return jsonify({"error": "Model returned invalid JSON", "detail": str(je), "raw": raw}) , 502
        return jsonify(parsed), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not connect to Ollama service: {e}"}), 500
    except Exception as e:
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
