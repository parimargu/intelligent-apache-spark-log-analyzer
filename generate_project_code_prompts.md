---

# 📘 LLM Prompt Templates

## Intelligent Apache Spark Log Analyzer

### **Code Generation Instruction Document**

---

## 📌 How to Use This Document

* Use **one prompt at a time** with an LLM (GPT-4, Claude, Gemini, OpenRouter, Ollama, etc.)
* Each prompt is **self-contained**
* Prompts are designed to generate:

  * ✅ Production-grade code
  * ✅ Clean project structure
  * ✅ Config-driven architecture
  * ✅ Enterprise best practices
* Backend and frontend are generated as **two independent applications**

---

## 🧠 GLOBAL SYSTEM PROMPT (RECOMMENDED)

> **Use this as a system message or prepend it to every prompt**

```text
You are a senior staff-level software engineer, data engineer, and solution architect.
You specialize in Python, FastAPI, Apache Spark, distributed systems, React, and enterprise SaaS platforms.
You write production-grade, secure, scalable, well-documented code.
Follow clean architecture, SOLID principles, and industry best practices.
Never generate pseudo-code — generate complete, runnable code.
```

---

## 🚀 PROMPT 1: Generate Overall Project Structure

```text
Based on the provided Project Development Document (PDD) for the "Intelligent Apache Spark Log Analyzer":

1. Design the complete project folder structure for:
   a) FastAPI backend application
   b) React frontend application

2. Follow clean architecture and enterprise best practices.

3. Clearly separate:
   - API layer
   - Business logic
   - Data access layer
   - Configuration
   - AI / LLM services
   - Background workers

4. Output ONLY the folder and file tree in Markdown format.
Do NOT generate any code yet.
```

---

## 🔧 PROMPT 2: Generate FastAPI Backend – Core Setup

```text
Generate a production-ready FastAPI backend application for the "Intelligent Apache Spark Log Analyzer" based strictly on the provided PDD.

Requirements:
- Python 3.x
- FastAPI
- Async endpoints
- SQLAlchemy ORM
- Config-driven (config.yaml)
- Environment variables via .env
- Supports SQLite and PostgreSQL (switchable)
- Clean architecture

Generate:
1. main.py
2. app initialization
3. config loader (YAML + env)
4. database connection module
5. dependency injection setup
6. basic health-check endpoint

Return the COMPLETE code for all files.
Include instructions to run the app.
```

---

## 📥 PROMPT 3: Backend – Log Ingestion APIs

```text
Generate FastAPI backend code for Spark log ingestion with the following features:

1. Manual log upload API
   - Supports .log, .txt, .gz, .zip
   - Handles large files safely

2. Folder-based ingestion
   - Configurable watch path
   - Background polling service

3. Programmatic ingestion
   - Secure REST API endpoint
   - API key authentication

4. Store raw logs metadata in the database

Requirements:
- Async processing
- Background tasks
- Proper validation
- Error handling

Return full code:
- API routes
- Services
- Background workers
- Models
```

---

## 🧩 PROMPT 4: Backend – Log Parsing & Normalization Engine

```text
Generate the log parsing and normalization module for Apache Spark logs.

The parser must:
- Detect log levels (INFO, WARN, ERROR, DEBUG)
- Extract timestamps, components, executors, messages
- Identify stack traces
- Normalize logs into a structured schema

Support logs from:
- Spark Standalone
- Spark on YARN
- Multiple languages (Python, Scala, Java, SQL, R)

Provide:
- Parser classes
- Utility functions
- Unit-test-ready structure
```

---

## 🤖 PROMPT 5: Backend – LLM Analysis & RAG Engine

```text
Generate an AI-powered analysis engine for Spark logs using LLMs.

Requirements:
- Pluggable LLM providers:
  - OpenAI
  - Gemini
  - Anthropic
  - Groq
  - OpenRouter
  - Local (Ollama)
- Config-driven provider selection
- Prompt templates for:
  - Root cause analysis
  - Memory issue diagnosis
  - Performance bottleneck detection
  - Configuration optimization

Implement:
- LLM client abstraction
- Prompt management
- RAG-ready architecture

Return complete production-ready code.
```

---

## 📊 PROMPT 6: Backend – Reports & Recommendations API

```text
Generate FastAPI APIs that:

1. Generate log-level reports
2. Provide drill-down views
3. Identify:
   - Language-specific exceptions
   - Memory issues
   - Performance bottlenecks
4. Suggest Spark configuration optimizations
5. Return AI-generated resolutions

Ensure:
- Pagination
- Filtering
- Search
- Clean API responses (DTOs)

Return full API and service layer code.
```

---

## 🧪 PROMPT 7: Backend – Security, Auth & Observability

```text
Enhance the FastAPI backend with:

1. JWT-based authentication
2. Role-based access control (Admin/User)
3. API key support for ingestion
4. Structured logging
5. Request tracing
6. Centralized error handling

Provide complete code additions and updates.
```

---

## 🎨 PROMPT 8: Generate React App – Core Setup

```text
Generate a production-grade React application for the "Intelligent Apache Spark Log Analyzer".

Requirements:
- React (latest stable)
- Functional components
- Hooks
- Clean folder structure
- API service layer
- Environment-based configuration

Generate:
1. Project setup
2. App layout
3. Routing
4. API client
5. Global state management

Return complete runnable code.
```

---

## 📤 PROMPT 9: React – Log Upload & Ingestion UI

```text
Generate React components for log ingestion:

1. Manual upload UI
2. Folder ingestion configuration UI
3. Programmatic ingestion token display
4. Upload progress
5. Validation & error handling

UI must be:
- Responsive
- User-friendly
- Enterprise-grade

Provide full component code.
```

---

## 📈 PROMPT 10: React – Dashboards & Reports

```text
Generate React dashboards to visualize:

- Log level summaries
- Error trends
- Exception categories
- Memory issues
- Performance bottlenecks

Features:
- Drill-down views
- Search & filters
- Timeline views

Use clean UI patterns and reusable components.
```

---

## 🧠 PROMPT 11: React – AI Insights & Recommendations

```text
Generate React UI for displaying:

- AI-generated root cause analysis
- Human-readable explanations
- Spark configuration recommendations
- Code optimization tips

Ensure:
- Clear readability
- Copy-to-clipboard
- Expand/collapse sections
```

---

## 📦 PROMPT 12: Packaging & Deployment

```text
Generate deployment-ready artifacts for both backend and frontend:

- Dockerfile
- docker-compose.yml
- Environment variable templates
- README.md with setup instructions

Ensure production best practices.
```

---

## ✅ Final Tip

If you want **maximum quality**, run prompts in this order:

1 → 2 → 3 → 4 → 5 → 6 → 7
then
8 → 9 → 10 → 11 → 12

---
