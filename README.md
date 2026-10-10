<<<<<<< HEAD
# FIN-SHIELD

AI-powered financial advertisement intelligence platform.

FIN-SHIELD helps investigators analyze advertisement copy, inspect extracted evidence, review explainable risk indicators, and explore potentially related advertisements. Scores and relationships are **not proof of fraud** and are **not a probability of crime**. All findings require human review.

The seeded dataset is **synthetic demonstration data**.

## Requirements

- Python 3.12 (Python 3.14 breaks pydantic-core and Pillow; use `python@3.12` from Homebrew)
- Node.js 20+
- No API keys are required for the main demonstration

OCR is optional. If Tesseract/`pytesseract` is missing, image submissions are stored and the limitation is reported; text analysis still works.

## Install

```bash
cd backend
python3.12 -m venv .venv        # use python@3.12 (Homebrew: /opt/homebrew/opt/python@3.12/bin/python3.12)
source .venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

## Seed the database

```bash
cd backend
source .venv/bin/activate
python seed.py
```

Safe to rerun: existing `seed_key` rows are skipped.

## Run

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

Open http://127.0.0.1:5173

## Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

```bash
cd frontend
npm run build
```

## Environment

Optional `backend/.env`:

```
DATABASE_URL=sqlite:////absolute/path/to/data/finshield.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SIMILARITY_THRESHOLD=0.72
```

Optional `frontend/.env`:

```
VITE_API_BASE_URL=
```

Leave `VITE_API_BASE_URL` empty when using the Vite proxy.
=======
# Fin-Shield
Al-Based Detection of Suspicious Financial Advertisements
>>>>>>> 3a7824a19659431711bdfccf0927b21c5967367c
