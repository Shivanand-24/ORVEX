# ORVEX — Enterprise Intelligence & Automation Platform

ORVEX is an enterprise-oriented AI platform designed to combine intelligent knowledge retrieval, AI agents, workflow automation, analytics, and enterprise security into a unified web application.

---

## Repository Architecture

- **`frontend/`**: React + TypeScript + Vite single-page application built with the ORVEX Pearl Enterprise Intelligence design system.
- **`backend/`**: Python 3.12 + FastAPI RESTful backend service with SQLAlchemy 2.x, asyncpg, Alembic migrations, and PostgreSQL 16 database foundation.
- **`docs/`**: Specifications, requirements, and database architecture documentation (`docs/database-architecture.md`).

---

## Getting Started

### 1. Frontend Setup

Requirements: Node.js 20.19+ or 22.12+ (required by Vite 8) and npm.

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (default: `http://localhost:5173`).

Useful scripts:
- `npm run build`: Production TypeScript check and Vite build
- `npm run lint`: Code quality linting via Oxlint
- `npm run preview`: Preview production build bundle

### 2. Backend & Database Setup

Requirements: Python 3.12+, Docker & Docker Compose (for local PostgreSQL 16).

#### Step 1: Start Local PostgreSQL 16 Container
```bash
# Run from repository root:
docker compose up -d
```

#### Step 2: Create & Activate Virtual Environment
```bash
cd backend
python -m venv .venv
```
- **Windows (PowerShell)**: `\.venv\Scripts\Activate.ps1`
- **macOS / Linux**: `source .venv/bin/activate`

#### Step 3: Install Dependencies & Configure Environment
```bash
pip install -r requirements.txt
cp .env.example .env
```

#### Step 4: Run Alembic Database Migrations
```bash
alembic upgrade head
```

#### Step 5: Start FastAPI Server
```bash
uvicorn app.main:app --reload --port 8000
```

Backend URLs:
- API Base: `http://localhost:8000/api/v1`
- Service Health: `http://localhost:8000/api/v1/health`
- Database Health: `http://localhost:8000/api/v1/health/db`
- Interactive OpenAPI Docs: `http://localhost:8000/api/v1/docs`

#### Step 6: Run Test Suite
```bash
pytest -v
```

---

## Technology Stack

- **Frontend**: React 19, TypeScript, Vite 8, Lucide React, Vanilla CSS
- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2, Pytest
- **Database**: PostgreSQL 16, SQLAlchemy 2.x, asyncpg, Alembic
- **AI Engine (Planned)**: LLM Orchestration, Embeddings, Vector Search
