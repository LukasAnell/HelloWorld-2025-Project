# AI Resume Reviewer — Deployment Guide

This repository contains a simple web UI (src/index.html) and a Flask backend (src/app.py) that calls an Ollama LLM to analyze resumes.

What you get:
- A single domain site at https://resumereviewer.lukasanell.org served by Caddy.
- The frontend (index.html) posts to /analyze.
- The backend proxies the request to the Ollama API and returns JSON. 
- CORS is enabled for the production domain and common localhost origins for local development.

## Components
- Frontend: static files in src/ (index.html, sample PDFs)
- Backend: Flask app in src/app.py
- LLM: Ollama container (image: ollama/ollama)
- Reverse proxy: Caddy with automatic HTTPS

## Quick start with Docker Compose
Prerequisites: Docker and Docker Compose, DNS A record for resumereviewer.lukasanell.org pointing to your host.

1. Pull/build and run services
   - From the project root:
     docker compose up -d --build

2. Access the site
   - https://resumereviewer.lukasanell.org
   - Upload a PDF or click a sample button (e.g., good.pdf), then click "Analyze This File".

## How it works
- The browser calls POST /analyze on the same origin. Caddy reverse proxies /analyze to the backend service.
- The backend sends a request to the Ollama service at http://ollama:11434/api/generate and returns the LLM JSON string.
- The UI parses the JSON and renders scores and comments.

## Configuration
- Change the LLM model: set MODEL_NAME in the backend container (defaults to llama3).
- Ollama URL: set OLLAMA_URL (defaults to http://ollama:11434 inside docker compose).
- Allowed origins (CORS): set ALLOWED_ORIGINS env var on the backend (comma-separated).

## Files added
- docker-compose.yml — orchestrates backend, caddy, and ollama
- Caddyfile — serves the site at resumereviewer.lukasanell.org and proxies /analyze
- src/Dockerfile — container for the Flask backend
- src/requirements.txt — includes Flask, Flask-Cors, requests, gunicorn

## Local development (without Docker)
- Start Ollama locally: ollama serve (default on http://localhost:11434)
- Install deps: pip install -r src/requirements.txt
- Run backend: python src/app.py (listens on http://localhost:5001)
- Serve index.html (any static server) and ensure it reaches http://localhost:5001/analyze (CORS is enabled for localhost).

## Notes
- Ensure your server can bind ports 80/443 for Caddy to obtain certificates via Let’s Encrypt (email set in Caddyfile).
- Optional: Caddy also exposes /ollama/* proxy for debugging the Ollama API.

---

## Windows PowerShell: Useful Commands (no Bash syntax)

These avoid Bash-only features like heredocs and $(...) subshells. Copy/paste as-is in PowerShell.

- Show backend logs
  - docker compose logs backend --tail=100

- Backend self-health (inside the container)
  - docker compose exec backend python -c "import urllib.request;print(urllib.request.urlopen('http://localhost:5001/health').read().decode())"

- Find your Compose network name and store it in a variable
  - $net = (docker network ls --format "{{.Name}}" | Select-String -Pattern "_default").ToString()

- Caddy → Backend (over Docker network)
  - docker run --rm --network $net curlimages/curl:8.11.1 -sS http://backend:5001/health

- Backend Analyze (POST) quick test
  - docker run --rm --network $net curlimages/curl:8.11.1 -sS -H "Content-Type: application/json" --data-binary '{"text":"hello"}' http://backend:5001/analyze

- Public health (browser)
  - https://resumereviewer.lukasanell.org/health  (expect {"status":"ok"})

If you accidentally add commentary to the end of a curl line (e.g., "Expected: {...}"), PowerShell will treat it as more arguments and curl will error. Put comments on a new line or use # for PowerShell comments.

---

## Optional: Standalone Ollama (no Traefik)

If you want to run Ollama by itself (outside the main stack), use the rewritten ollama/docker-compose.yml. It exposes only port 11434 and stores models in a volume. Example:

- cd ollama
- docker compose up -d
- Test locally from the host:
  - curl -sS http://localhost:11434/api/version

Ensure this standalone Ollama does not conflict with the main stack if both are running; the main stack already includes an Ollama service on the internal Docker network.
