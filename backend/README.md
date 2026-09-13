# ORVEX Backend Foundation

Welcome to the backend foundation for **ORVEX**, an Enterprise Intelligence & Automation Platform.

## Overview

The ORVEX backend is a high-performance RESTful API service built with **Python 3.12+** and **FastAPI**. It is designed to serve as the backend application foundation connecting the React enterprise frontend with security, data persistence, AI orchestration, knowledge retrieval (RAG), and agentic workflows in future milestones.

### Why FastAPI?

- **High Performance**: Asynchronous Python micro-framework powered by Starlette and Pydantic.
- **Type Safety & Data Validation**: Native Pydantic integration enforces strict request/response data contracts.
- **Automatic OpenAPI Documentation**: Generates interactive API docs (`/api/v1/docs` and `/api/v1/redoc`) out of the box.
- **Developer Ergonomics**: Modern Python async capabilities, intuitive routing, and lightweight footprint.

---

## Directory Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # Application initialization & setup
│   │
│   ├── core/              # Configuration, CORS, error handlers
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── cors.py
│   │   └── errors.py
│   │
│   ├── api/               # API route definitions & versioning
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py  # Master v1 router
│   │       └── health.py  # Health check endpoint
│   │
│   └── schemas/           # Pydantic data schemas
│       ├── __init__.py
│       └── health.py
│
├── tests/                 # Pytest test suite
│   ├── __init__.py
│   └── test_health.py
│
├── .env.example           # Environment template configuration
├── .gitignore             # Python/Git ignore rules
├── requirements.txt       # Production & dev dependencies
└── README.md              # Backend documentation
```

---

## Getting Started

### 1. Requirements

- Python **3.12** or higher installed.

### 2. Create Virtual Environment

Navigate to the `backend/` directory and create a Python virtual environment:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell)**:
  ```powershell
  \.venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  \.venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies

With the virtual environment activated, install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to create your local `.env` configuration:

```bash
cp .env.example .env
```

Default settings in `.env.example`:

```env
APP_NAME="ORVEX API"
APP_ENV="development"
API_V1_PREFIX="/api/v1"
CORS_ORIGINS=["http://localhost:5173"]
LOG_LEVEL="INFO"
```

> **Note**: Do not commit your `.env` file to version control.

---

## Running Development Server

Start the Uvicorn development server with auto-reload enabled:

```bash
uvicorn app.main:app --reload --port 8000
```

Once running:
- Health Endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Swagger OpenAPI Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- ReDoc Docs: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

---

## Running Tests

Execute unit tests using `pytest`:

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

---

## API Health Endpoint

### `GET /api/v1/health`

Returns operational status of the backend API.

#### Response (HTTP 200 OK):

```json
{
  "status": "ok",
  "service": "ORVEX API",
  "version": "v1"
}
```

---

## Future Roadmap

The backend foundation will evolve across future milestones:

1. **Database Layer**: PostgreSQL integration, SQLAlchemy ORM models, and Alembic migrations.
2. **Authentication & RBAC**: OAuth2 / JWT authentication, user management, role-based access control.
3. **AI Assistant & RAG Engine**: Vector search, embeddings, document ingestion, and LLM orchestration.
4. **Agent & Workflow Engine**: Autonomous AI agent execution loops and workflow graph runner.
5. **Analytics & Audit Logging**: Usage telemetry, execution logs, and compliance audit trail.
