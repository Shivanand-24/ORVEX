# ORVEX

## Frontend setup

This repository currently contains the React frontend only; no backend, authentication, or external AI integration is connected yet.

Requirements: Node.js 20.19+ or 22.12+ (required by Vite 8) and npm.

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. Use `npm run build` for a production type-check/build, `npm run lint` for Oxlint, and `npm run preview` to preview the production bundle.

## Current frontend architecture

- `frontend/src/routes`: browser routes and route safety fallbacks.
- `frontend/src/layouts` and `components`: shared application shell.
- `frontend/src/pages`: feature screens.
- `frontend/src/types`: small shared frontend domain types.
- `frontend/src/services`: in-memory repositories that can later be replaced by API-backed implementations.

The dashboard and workflow builder are frontend prototypes. Knowledge, Assistant, and Analytics are still placeholders. Product requirements are in `docs/requirements.md`.

## Enterprise AI Intelligence & Automation Platform

ORVEX is an enterprise-oriented AI platform designed to combine
intelligent knowledge retrieval, AI agents, workflow automation,
analytics, and enterprise security into a unified web application.

## Vision

Build a production-ready AI platform capable of helping organizations
retrieve knowledge, analyze information, automate workflows, and make
better data-driven decisions.

## Core Capabilities

- AI Assistant
- Retrieval-Augmented Generation (RAG)
- AI Agents
- Tool Calling
- Workflow Automation
- Document Intelligence
- Data Analytics
- Role-Based Access Control
- Human-in-the-Loop Approval
- Audit Logging
- AI Evaluation
- Cloud Deployment

## Planned Technology Stack

### Frontend
- React
- TypeScript
- HTML
- CSS

### Backend
- Python
- FastAPI

### Database
- PostgreSQL

### AI
- Large Language Models
- RAG
- Embeddings
- Vector Search
- Agentic AI

### DevOps
- Git
- GitHub
- Docker
- CI/CD
- Cloud Deployment

## Project Status

🚧 Currently under active development.
