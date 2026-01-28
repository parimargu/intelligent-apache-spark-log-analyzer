# Backend - Intelligent Apache Spark Log Analyzer

FastAPI backend for log ingestion, parsing, AI analysis, and reporting.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/logs/upload` - Upload log files
- `GET /api/v1/logs` - List ingested logs
- `GET /api/v1/reports` - Get analysis reports
- `POST /api/v1/analyze` - Trigger AI analysis
