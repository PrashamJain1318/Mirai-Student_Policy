# MirAI Student Policy Advisor — Backend

For complete documentation, architecture diagrams, local setup, and evaluation details, please see the [Root README.md](../README.md).

### Quickstart (Backend):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # Add your GOOGLE_API_KEY
python scripts/ingest_handbook.py
uvicorn backend:app --reload --host 127.0.0.1 --port 8000
```

### Running Backend Tests:
```bash
pytest -q
```
