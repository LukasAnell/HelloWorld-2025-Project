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
    ---
    Resume Rubric
    There are 5 categories separated by the '/' character with a maximum score of 5 points for each category for a total of 25 points.


Content/
Relevance
Achievements/
Results
Skills/
Keywords
Organization/
Formatting
Professionalism

score of 0

Missing key sections (e.g., experiences, skills, education, or activities)./
Experiences listed only as duties or vague activities, no outcomes./
No skills section included./
Resume is unstructured, confusing, or unreadable./
Multiple spelling/grammar errors; tone unprofessional.

score of 1

Sections included but mostly irrelevant or generic (e.g., listing hobbies instead of relevant roles)./
Mentions involvement but without showing contributions or results./
Skills are vague and generic (e.g., “hardworking,” “team player”) with no context./
Some structure, but formatting is inconsistent (e.g., different fonts, missing sections, uneven spacing). (more than a page)/
Frequent minor errors; language informal or inconsistent.

score of 2

Contains some relevant roles/activities but lacks clarity or alignment with the target purpose./
Includes some achievements, but they are general (e.g., “helped with events”)./
Skills included but not clearly tied to experiences or purpose (e.g., listing “coding” but no mention in experiences)./
Resume is mostly readable but cluttered, or sections are poorly separated./
Some errors remain; tone somewhat professional but uneven.

score of 3

Resume includes experiences (work, volunteer, academic, or club) that are somewhat related to the goal (job, club, scholarship)./
At least half of experiences show results or contributions (e.g., “organized meetings,” “led 5-member team”)./
Resume lists at least 5 relevant skills (academic, technical, leadership, or organizational)./
Resume is clear and logically structured with consistent headings, bullet points, and order./
Mostly professional tone; no more than 1–2 minor errors.

score of 4

Resume includes well-chosen experiences clearly relevant to the purpose, with mostly specific details./
Most experiences highlight specific contributions or measurable outcomes (numbers, growth, awards, leadership results)./
Skills are well-balanced (hard + soft skills) and connect to experiences listed./
Resume is professional-looking, easy to scan, with effective use of white space and bullet points./
Professional, error-free in most places, fully updated with recent experiences.

score of 5

Resume is fully relevant and tailored — every section (summary, experiences, skills) supports the intended goal, whether job, club, or general application./
All experiences emphasize impact with clear, measurable, or concrete results (e.g., “Raised $500 in fundraising,” “Increased club membership by 30%”)./
Skills are highly relevant, specific, and reflect what the role, club, or opportunity seeks (e.g., “Python, public speaking, event planning, budget management”)./
Resume is polished, clean, consistent, with professional formatting and clear file naming (e.g., “Lastname_Firstname_Resume.pdf” or similar)./
Completely error-free, professional tone throughout, up-to-date, polished, and shows attention to detail.



    ---

    Resume Text:
    ---
    {resume_text}
    ---
    
    Rubric:
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

        # Ollama returns the JSON response as a string in the 'response' key
        analysis_result = response.json()
        return analysis_result['response'], 200, {'Content-Type': 'application/json'}

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
