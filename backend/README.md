# ORVEX Backend & Database Layer

Welcome to the backend foundation for **ORVEX**, an Enterprise Intelligence & Automation Platform.

## Overview

The ORVEX backend is a high-performance RESTful API service built with **Python 3.12+**, **FastAPI**, **SQLAlchemy 2.x**, **asyncpg**, and **PostgreSQL 16**.

### Core Stack & Architecture

- **Web Framework**: FastAPI (powered by Starlette & Pydantic v2)
- **ORM & Database**: SQLAlchemy 2.x (AsyncEngine, AsyncSession) with `asyncpg` driver
- **Migrations**: Alembic with version-controlled revision scripts
- **Database Engine**: PostgreSQL 16 (Local via Docker Compose)
- **Testing**: Pytest with metadata & connection health tests

---

## Directory Structure

```text
backend/
├── alembic/               # Alembic database migrations
│   ├── versions/
│   │   └── 0001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
│
├── app/
│   ├── main.py            # FastAPI app factory & lifespan
│   │
│   ├── core/              # Configuration, CORS, error handling
│   │   ├── config.py
│   │   ├── cors.py
│   │   └── errors.py
│   │
│   ├── db/                # Database engine & session providers
│   │   ├── base.py        # Base metadata & model export
│   │   └── session.py     # AsyncSessionLocal & get_db_session dependency
│   │
│   ├── models/            # SQLAlchemy 2.x declarative models (14 tables)
│   │   ├── base.py        # Base & TimestampMixin
│   │   ├── organization.py # Organization
│   │   ├── user.py         # User
│   │   ├── membership.py   # OrganizationMembership
│   │   ├── knowledge.py    # KnowledgeSource & KnowledgeDocument
│   │   ├── assistant.py    # Conversation & AssistantMessage
│   │   ├── agent.py        # Agent, AgentKnowledgeSource & AgentTool
│   │   ├── workflow.py     # Workflow, WorkflowStep & WorkflowExecution
│   │   └── audit.py        # AuditLog
│   │
│   ├── repositories/      # Data access layer (AsyncSession CRUD)
│   │   ├── organization_repository.py
│   │   ├── user_repository.py
│   │   ├── membership_repository.py
│   │   ├── knowledge_source_repository.py
│   │   ├── knowledge_document_repository.py
│   │   ├── conversation_repository.py
│   │   ├── message_repository.py
│   │   └── agent_repository.py
│   │
│   ├── services/          # Business logic layer
│   │   ├── organization_service.py
│   │   ├── user_service.py
│   │   ├── membership_service.py
│   │   ├── knowledge_source_service.py
│   │   ├── knowledge_document_service.py
│   │   ├── assistant_conversation_service.py
│   │   ├── assistant_message_service.py
│   │   └── agent_service.py
│   │
│   ├── api/v1/            # API endpoints & routers
│   │   ├── router.py      # Master v1 router
│   │   ├── health.py      # Health check endpoints
│   │   ├── organizations.py # Organization CRUD router
│   │   ├── users.py         # User CRUD router
│   │   ├── memberships.py   # Organization Membership router
│   │   ├── knowledge.py     # Knowledge Sources & Documents router
│   │   ├── assistant.py     # Assistant Conversations & Messages router
│   │   └── agents.py        # Agents & Relationships router
│   │
│   └── schemas/           # Pydantic request/response schemas
│       ├── health.py
│       ├── organization.py
│       ├── user.py
│       ├── membership.py
│       ├── knowledge.py
│       ├── assistant.py
│       └── agent.py
│
├── tests/                 # Pytest suite
│   ├── test_health.py
│   ├── test_db_models.py
│   ├── test_db_health.py
│   ├── test_organizations_api.py
│   ├── test_users_api.py
│   ├── test_memberships_api.py
│   ├── test_knowledge_sources_api.py
│   ├── test_knowledge_documents_api.py
│   ├── test_assistant_api.py
│   └── test_agent_api.py
│
├── alembic.ini            # Alembic configuration
├── .env.example           # Environment template configuration
├── requirements.txt       # Python dependencies
└── README.md
```

---

## Getting Started

### 1. Requirements

- Python **3.12+**
- Docker & Docker Compose (for local PostgreSQL 16)

### 2. Create & Activate Virtual Environment

```bash
cd backend
python -m venv .venv
```

Activate:
- **Windows (PowerShell)**: `\.venv\Scripts\Activate.ps1`
- **macOS / Linux**: `source .venv/bin/activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Local PostgreSQL Setup (Docker Compose)

Start the PostgreSQL 16 container from the project root:

```bash
# From project root directory:
docker compose up -d
```

To stop PostgreSQL:
```bash
docker compose down
```

### 5. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Default connection settings:

```env
DATABASE_URL="postgresql+asyncpg://orvex_user:orvex_dev_secret@localhost:5432/orvex_db"
SYNC_DATABASE_URL="postgresql+psycopg2://orvex_user:orvex_dev_secret@localhost:5432/orvex_db"
```

### 6. Run Database Migrations (Alembic)

Apply all 14 schema tables to the running PostgreSQL database:

```bash
alembic upgrade head
```

---

## Data Access Layer APIs & Payloads (Phase 2B)

### Organizations API (`/api/v1/organizations`)

- `POST /api/v1/organizations`: Create new organization (requires `name` and unique `slug`).
- `GET /api/v1/organizations`: List all organizations.
- `GET /api/v1/organizations/{id}`: Get organization by UUID.
- `PATCH /api/v1/organizations/{id}`: Update organization `name` or `slug`.

**Example Create Request:**
```json
{
  "name": "Acme Intelligence Corp",
  "slug": "acme-corp"
}
```

### Users API (`/api/v1/users`)

- `POST /api/v1/users`: Create new global user identity (requires valid, unique `email` and `full_name`).
- `GET /api/v1/users`: List all users.
- `GET /api/v1/users/{id}`: Get user by UUID.

**Example Create Request:**
```json
{
  "email": "alice@acme.com",
  "full_name": "Alice Smith"
}
```

### Memberships API (`/api/v1/organizations/{organization_id}/members`)

- `POST /api/v1/organizations/{organization_id}/members`: Add user to organization with role (`admin`, `member`, or `analyst`).
- `GET /api/v1/organizations/{organization_id}/members`: List all members of an organization.
- `PATCH /api/v1/organizations/{organization_id}/members/{membership_id}`: Update member role.
- `DELETE /api/v1/organizations/{organization_id}/members/{membership_id}`: Remove member from organization (preserves User and Organization entities).

**Example Add Member Request:**
```json
{
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "role": "admin"
}
```

### Knowledge Sources API (`/api/v1/knowledge/sources`) (Phase 2C)

- `POST /api/v1/knowledge/sources`: Create new knowledge source collection for an organization.
- `GET /api/v1/knowledge/sources`: List knowledge sources, optionally filtered by `organization_id`.
- `GET /api/v1/knowledge/sources/{source_id}`: Retrieve knowledge source by UUID (with optional `organization_id` tenant isolation).
- `PATCH /api/v1/knowledge/sources/{source_id}`: Update collection `name` or `description`.
- `DELETE /api/v1/knowledge/sources/{source_id}`: Delete collection (cascades delete to all attached documents).

**Example Create Request:**
```json
{
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Engineering Runbooks",
  "description": "Troubleshooting guides and system operational procedures."
}
```

### Knowledge Documents API (`/api/v1/knowledge/...`) (Phase 2C)

- `POST /api/v1/knowledge/sources/{source_id}/documents`: Create document metadata under a knowledge source.
- `GET /api/v1/knowledge/sources/{source_id}/documents`: List all documents belonging to a knowledge source.
- `GET /api/v1/knowledge/documents/{document_id}`: Retrieve a single knowledge document by UUID.
- `PATCH /api/v1/knowledge/documents/{document_id}`: Update document metadata or lifecycle status.
- `DELETE /api/v1/knowledge/documents/{document_id}`: Delete a knowledge document (parent source remains intact).

**Example Create Request:**
```json
{
  "name": "Architecture Overview 2026.pdf",
  "file_type": "PDF",
  "size_bytes": 1048576,
  "summary": "Technical system architecture overview.",
  "status": "Pending",
  "readiness": "NotIndexed"
}
```

#### Knowledge Lifecycle & Multi-Tenant Isolation
- **Processing Statuses:** `pending`, `processing`, `processed`, `failed` (Frontend: `Pending`, `Processing`, `Processed`, `Failed`).
- **Indexing Readiness:** `not_indexed`, `indexing`, `indexed`, `index_failed` (Frontend: `NotIndexed`, `Indexing`, `Indexed`, `IndexFailed`).
- **Lifecycle Rule:** Document must reach `processed` state before transitioning readiness to `indexing` or `indexed`.
- **Tenant Isolation:** Cross-organization source queries, document lookups, and cross-tenant document attachments are strictly rejected with 404/400 errors.
- **Current Limitation:** Because authentication is deferred to later milestones, `organization_id` is supplied explicitly at the API boundary.

### Assistant API (`/api/v1/assistant/...`) (Phase 2D)

#### Conversations (`/api/v1/assistant/conversations`)
- `POST /api/v1/assistant/conversations`: Create a new conversation session for an organization.
- `GET /api/v1/assistant/conversations`: List conversations, optionally filtered by `organization_id`.
- `GET /api/v1/assistant/conversations/{conversation_id}`: Retrieve conversation by UUID (with optional `organization_id` tenant check).
- `PATCH /api/v1/assistant/conversations/{conversation_id}`: Update conversation `title`.
- `DELETE /api/v1/assistant/conversations/{conversation_id}`: Delete conversation (cascades deletion to all attached messages).

**Example Create Request:**
```json
{
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "title": "Onboarding Architecture Discussion"
}
```

#### Messages (`/api/v1/assistant/...`)
- `POST /api/v1/assistant/conversations/{conversation_id}/messages`: Persist a user, assistant, or system message inside a conversation.
- `GET /api/v1/assistant/conversations/{conversation_id}/messages`: List all messages in a conversation ordered chronologically.
- `GET /api/v1/assistant/messages/{message_id}`: Retrieve a single message by UUID.

**Example Create Message Request:**
```json
{
  "role": "user",
  "content": "What can ORVEX help me automate?",
  "tokens_used": 0,
  "latency_ms": 0
}
```

#### Assistant Persistence & Tenant Isolation
- **Organization Ownership:** Every conversation is owned by an organization and user.
- **Message Inheritance:** Messages inherit tenant scope directly from their parent conversation.
- **Role Validation:** Enforces database role check constraint (`user`, `assistant`, `system`).
- **Tenant Isolation:** Cross-organization conversation queries, message listings, message retrieval, and message postings return `404 Not Found`.
- **Current Limitation (Persistence First):** Messages are persisted reliably in the database; real AI/LLM response generation, streaming, and RAG execution will be attached in subsequent milestones.

### Agents API (`/api/v1/agents/...`) (Phase 2E)

#### Agents CRUD (`/api/v1/agents`)
- `POST /api/v1/agents`: Register and configure a new AI Agent for an organization (with optional initial tools and knowledge sources).
- `GET /api/v1/agents`: List AI agents with filtering by `organization_id`, `domain`, `status`, and pagination (`skip`, `limit`).
- `GET /api/v1/agents/{agent_id}`: Retrieve agent details by UUID (with optional `organization_id` tenant check).
- `PATCH /api/v1/agents/{agent_id}`: Update agent fields (`name`, `description`, `domain`, `status`, `system_instructions`, `require_approval`).
- `DELETE /api/v1/agents/{agent_id}`: Delete an agent (cascades deletion to attached tools and knowledge source associations).

**Example Create Request:**
```json
{
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Research Sentinel",
  "description": "Autonomous research and document synthesis worker.",
  "domain": "Research",
  "status": "Active",
  "system_instructions": "Analyze documents and pull relevant knowledge citations.",
  "require_approval": false,
  "tools": ["Document Parser", "RAG Retrieval"],
  "knowledge_source_ids": ["7d2b4510-37cb-4b36-a36c-941e3d3fa1cf"]
}
```

#### Relationships (`/api/v1/agents/{agent_id}/...`)
- `GET /api/v1/agents/{agent_id}/knowledge-sources`: List knowledge sources attached to this agent.
- `POST /api/v1/agents/{agent_id}/knowledge-sources`: Attach a knowledge source (`source_id: UUID`) to this agent.
- `DELETE /api/v1/agents/{agent_id}/knowledge-sources/{source_id}`: Detach a knowledge source from this agent.
- `GET /api/v1/agents/{agent_id}/tools`: List tool names attached to this agent.
- `POST /api/v1/agents/{agent_id}/tools`: Attach a tool identifier (`tool_name: str`) to this agent.
- `DELETE /api/v1/agents/{agent_id}/tools/{tool_name}`: Detach a tool identifier from this agent.

#### Agent Persistence & Multi-Tenant Isolation
- **Organization Boundary:** Every agent belongs to exactly one organization.
- **Creator User Resolution:** Requires `created_by_user_id` (safely falls back to an organization member if omitted).
- **Cross-Tenant Knowledge Source Protection:** Attempting to attach a KnowledgeSource from a different organization is strictly rejected with `404 Not Found`.
- **Eager Loading Performance:** Repositories use `selectinload` for `tools`, `knowledge_sources`, and `creator` to eliminate N+1 query overhead.
- **Current Limitation (Management Only):** This milestone establishes database persistence for Agents and their associations. Runtime execution loops, LLM calls, tool execution, and RAG retrieval will be connected in future milestones.

---

## Running Development Server & Tests

### Start FastAPI Server

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints:
- API Base: `http://localhost:8000/api/v1`
- Service Health: `http://localhost:8000/api/v1/health`
- Database Health: `http://localhost:8000/api/v1/health/db`
- Interactive OpenAPI Docs: `http://localhost:8000/api/v1/docs`

### Run Test Suite

The test suite runs using in-memory SQLite (`aiosqlite`) and does not require a running PostgreSQL server:

```bash
pytest -v
```

All 95 backend unit and API integration tests cover:
- FastAPI router, service, and repository layers for Organizations, Users, Memberships, Knowledge, Assistant, and Agents
- Domain validation (emails, slugs, valid roles, agent domains, valid statuses, lifecycle state transitions)
- Conflict detection (duplicate slugs, duplicate emails, duplicate org memberships)
- Entity not found handling (404 response codes)
- Strict cross-organization access control & tenant isolation
- CASCADE & preservation behavior on deletion


---

## Database Architecture (14 Tables)

| Entity Table | Primary Key | Key Columns / Constraints |
| :--- | :--- | :--- |
| `organizations` | UUID | `slug` (UNIQUE) |
| `users` | UUID | `email` (UNIQUE) |
| `organization_memberships` | UUID | `(organization_id, user_id)` UNIQUE, role CHECK |
| `knowledge_sources` | UUID | `organization_id` (FK CASCADE) |
| `knowledge_documents` | UUID | `source_id` (FK CASCADE), `processing_status`, `indexing_status` |
| `conversations` | UUID | `user_id` (FK CASCADE), `organization_id` (FK CASCADE) |
| `messages` | UUID | `conversation_id` (FK CASCADE), role CHECK |
| `agents` | UUID | `organization_id` (FK CASCADE), `created_by_user_id` (FK RESTRICT) |
| `agent_knowledge_sources` | Composite `(agent_id, source_id)` | FK CASCADE |
| `agent_tools` | Composite `(agent_id, tool_name)` | Application Tool Registry mapping |
| `workflows` | UUID | `organization_id` (FK CASCADE), `created_by_user_id` (FK RESTRICT) |
| `workflow_steps` | UUID | `workflow_id` (FK CASCADE), `config` (JSONB), `next_step_ids` (JSONB) |
| `workflow_executions` | UUID | `workflow_id` (FK CASCADE), `execution_log` (JSONB) |
| `audit_logs` | UUID | `organization_id` (FK CASCADE), `actor_id` (FK SET NULL), `details` (JSONB) |

