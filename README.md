# Rendezvous Backend

FastAPI server for the Rendezvous trend analysis service.

## Requirements

- Python 3.11 or newer

## Setup

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Run

```bash
./scripts/dev.sh
```

The API starts at `http://127.0.0.1:8000`.

## Health Check

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response:

```json
{"status":"ok"}
```

## Test

```bash
.venv/bin/python -m pytest
```
