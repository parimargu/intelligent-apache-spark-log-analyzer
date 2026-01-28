# Intelligent Apache Spark Log Analyzer

AI-powered log analysis platform for Apache Spark applications. Automatically parses, analyzes, and provides intelligent insights for Spark logs using advanced LLM models.

## Features

- **Multi-format Support**: Parse `.log`, `.txt`, `.gz`, and `.zip` files
- **Spark Mode Detection**: Standalone, YARN, Kubernetes, Local
- **Language Detection**: Python, Scala, Java, SQL, R
- **AI Analysis**: Root cause analysis, memory optimization, performance tuning
- **Multiple LLM Providers**: OpenAI, Gemini, Anthropic, Groq, OpenRouter, Ollama
- **Real-time Dashboard**: Monitor errors, warnings, and trends
- **REST API**: Programmatic access with API key authentication

## Quick Start

### Admin Login
- **URL**: http://localhost:3000/login
- **Email**: `admin@example.com`
- **Password**: `admin123`

### Using Docker (Recommended)

```bash
# Clone and start
git clone <repo-url>
cd intelligent-apache-spark-log-analyzer

# Set environment variables
cp backend/.env.example backend/.env
# Edit .env with your API keys

# Start with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
intelligent-apache-spark-log-analyzer/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── config/         # Configuration
│   │   ├── core/           # Security, dependencies
│   │   ├── db/             # Database setup
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry
│   ├── config.yaml         # YAML configuration
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── context/        # React context
│   │   └── services/       # API services
│   └── package.json
└── docker-compose.yml      # Docker deployment
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login (get JWT) |
| `/api/v1/ingestion/upload` | POST | Upload log file |
| `/api/v1/logs` | GET | List log files |
| `/api/v1/logs/{id}/entries` | GET | Get log entries |
| `/api/v1/analysis` | POST | Run AI analysis |
| `/api/v1/reports/dashboard` | GET | Dashboard summary |

Full API docs available at `/docs` when running.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./data/spark_analyzer.db` |
| `SECRET_KEY` | JWT secret key | Random 32 chars |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GROQ_API_KEY` | Groq API key | - |

### LLM Providers

Configure your preferred LLM provider in `config.yaml`:

```yaml
llm:
  default_provider: openai  # or gemini, anthropic, groq, ollama
  default_model: gpt-4
```

## Architecture

- **Backend**: FastAPI with async SQLAlchemy, JWT auth
- **Frontend**: React 18 with Vite, Recharts for visualization
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Deployment**: Docker Compose with nginx reverse proxy

## License

MIT License
