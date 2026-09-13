# ORVEX — Enterprise Intelligence & Automation Platform

ORVEX is an enterprise-oriented AI platform designed to combine intelligent knowledge retrieval, AI agents, workflow automation, analytics, and enterprise security into a unified web application.

---

## Repository Architecture

- **`frontend/`**: React + TypeScript + Vite single-page application built with the ORVEX Pearl Enterprise Intelligence design system.
- **`backend/`**: Python + FastAPI RESTful backend service foundation providing configuration, CORS, error handling, health endpoints, and automated tests.
- **`docs/`**: Product specifications, requirements, and architecture documentation.

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

### 2. Backend Setup

Requirements: Python 3.12+.

```bash
cd backend
python -m venv .venv
```

Activate environment:
- **Windows (PowerShell)**: `\.venv\Scripts\Activate.ps1`
- **macOS / Linux**: `source .venv/bin/activate`

Install dependencies and start dev server:

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Backend URLs:
- API Base: `http://localhost:8000/api/v1`
- Health Endpoint: `http://localhost:8000/api/v1/health`
- Interactive OpenAPI Docs: `http://localhost:8000/api/v1/docs`

Run backend test suite:

```bash
pytest
```

---

## Core Capabilities & Vision

- AI Assistant & Retrieval-Augmented Generation (RAG)
- AI Agents & Graph Workflows
- Document Intelligence & Search
- Data Analytics & Telemetry
- Role-Based Access Control (RBAC) & Enterprise Security

---

## Technology Stack

- **Frontend**: React 19, TypeScript, Vite 8, Lucide React, Vanilla CSS
- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2, Pytest
- **Database (Planned)**: PostgreSQL
- **AI Engine (Planned)**: LLM Orchestration, Embeddings, Vector Search
