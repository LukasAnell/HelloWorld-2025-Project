# src/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

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
    Analyze the following resume text and provide feedback.
    Score it from 1 to 5 in these categories:
    - Content / Relevance
    - Achievements / Results
    - Skills / Keywords
    - Organization / Formatting
    - Professionalism

    Also, provide a list of 3-5 specific, actionable comments for improvement.

    Format the response as a JSON object with two keys: "scores" and "comments".
    The "scores" key should contain an array of objects, where each object has "name", "score", and "max" keys.
    The "comments" key should contain an array of strings.

    Resume Text:
    ---
    {resume_text}
    ---
    """

    try:
        # The payload to send to Ollama's API
        ollama_payload = {
            "model": MODEL_NAME,  # Configurable via env
            "prompt": prompt,
            "format": "json",   # Request JSON output from Ollama
            "stream": False
        }

        # Forward the request to the Ollama container
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=ollama_payload)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Ollama returns the JSON response as a string in the 'response' key
        analysis_result = response.json()
        return analysis_result['response'], 200, {'Content-Type': 'application/json'}

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not connect to Ollama service: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
