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
│   │   ├── 0001_initial_schema.py
│   │   └── 0002_agent_executions.py
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
│   ├── execution/         # Agent execution foundation primitives
│   │   ├── lifecycle.py   # State machine, ExecutionStatus & transition validation
│   │   ├── context.py     # Ephemeral runtime ExecutionContext
│   │   ├── interfaces.py  # Provider contracts (KnowledgeProvider, ToolRegistry, LLMProvider)
│   │   ├── resolver.py    # Agent configuration & tenant resolver
│   │   └── approval.py    # Human-in-the-loop approval manager
│   │
│   ├── workflows/         # Workflow orchestration & DAG validation primitives
│   │   ├── dag.py         # DAG validation (cycle, reachability, root detection, limits)
│   │   └── adapters.py    # Orchestration contracts (Agent, Knowledge, Action, Condition)
│   │
│   ├── models/            # SQLAlchemy 2.x declarative models (15 tables)
│   │   ├── base.py        # Base & TimestampMixin
│   │   ├── organization.py # Organization
│   │   ├── user.py         # User
│   │   ├── membership.py   # OrganizationMembership
│   │   ├── knowledge.py    # KnowledgeSource & KnowledgeDocument
│   │   ├── assistant.py    # Conversation & AssistantMessage
│   │   ├── agent.py        # Agent, AgentKnowledgeSource & AgentTool
│   │   ├── agent_execution.py # AgentExecution
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
│   │   ├── agent_repository.py
│   │   ├── agent_execution_repository.py
│   │   └── workflow_repository.py
│   │
│   ├── services/          # Business logic layer
│   │   ├── organization_service.py
│   │   ├── user_service.py
│   │   ├── membership_service.py
│   │   ├── knowledge_source_service.py
│   │   ├── knowledge_document_service.py
│   │   ├── assistant_conversation_service.py
│   │   ├── assistant_message_service.py
│   │   ├── agent_service.py
│   │   ├── agent_execution_service.py
│   │   └── workflow_service.py
│   │
│   ├── api/v1/            # API endpoints & routers
│   │   ├── router.py      # Master v1 router
│   │   ├── health.py      # Health check endpoints
│   │   ├── organizations.py # Organization CRUD router
│   │   ├── users.py         # User CRUD router
│   │   ├── memberships.py   # Organization Membership router
│   │   ├── knowledge.py     # Knowledge Sources & Documents router
│   │   ├── assistant.py     # Assistant Conversations & Messages router
│   │   ├── agents.py        # Agents & Relationships router
│   │   ├── executions.py    # Agent Execution Lifecycle & Governance router
│   │   └── workflows.py     # Workflows & Orchestration router
│   │
│   └── schemas/           # Pydantic request/response schemas
│       ├── health.py
│       ├── organization.py
│       ├── user.py
│       ├── membership.py
│       ├── knowledge.py
│       ├── assistant.py
│       ├── agent.py
│       ├── agent_execution.py
│       └── workflow.py
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
│   ├── test_agent_api.py
│   ├── test_agent_execution.py
│   └── test_workflow_api.py
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

#### Agent Execution Foundation (`/api/v1/...`)
- `POST /api/v1/agents/{agent_id}/executions`: Trigger an execution run for an active agent.
- `GET /api/v1/agents/{agent_id}/executions`: List executions for an agent (with optional status filtering & pagination).
- `GET /api/v1/executions/{execution_id}`: Retrieve detailed execution state, output, and telemetry metrics.
- `POST /api/v1/executions/{execution_id}/approve`: Grant human approval to a run paused in `waiting_for_approval`.
- `POST /api/v1/executions/{execution_id}/cancel`: Cancel a pending or running execution run.

#### Execution Governance & Multi-Tenant Isolation
- **Domain Lifecycle States:** Enforced strict state transitions (`pending`, `running`, `waiting_for_approval`, `completed`, `failed`, `cancelled`).
- **Human-in-the-Loop Approval:** When `Agent.require_approval=True`, executions pause in `waiting_for_approval`. Only members of the owning organization can approve runs.
- **Audit Logging:** Every state transition automatically emits privacy-safe metadata audit logs (`agent.execution.*`) without leaking raw user prompts or confidential model outputs.
- **Cascade Deletion:** Deleting an Agent cleanly cascades and removes all associated execution runs.

### Workflows API (`/api/v1/workflows/...`) (Phase 2G)

#### Workflows CRUD & Steps Management (`/api/v1/workflows`)
- `POST /api/v1/workflows`: Create workflow definition with optional initial steps. Validates DAG structure if steps are provided.
- `GET /api/v1/workflows`: List workflows filtered by `organization_id`, `status` (`draft`, `active`, `paused`), and pagination (`skip`, `limit`).
- `GET /api/v1/workflows/{workflow_id}`: Retrieve workflow details including all configured steps and recent execution summaries.
- `PATCH /api/v1/workflows/{workflow_id}`: Update workflow metadata (`name`, `description`).
- `PATCH /api/v1/workflows/{workflow_id}/status`: Toggle workflow status (`draft`, `active`, `paused`).
- `PUT /api/v1/workflows/{workflow_id}/steps`: Synchronize full set of steps with complete DAG graph validation.
- `DELETE /api/v1/workflows/{workflow_id}`: Delete workflow (cascades deletion to steps and execution runs).

**Example Create Workflow Request:**
```json
{
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Customer Support Escalation",
  "description": "Orchestrates issue ingestion, retrieval, agent triage, and approval.",
  "status": "draft",
  "steps": [
    {
      "step_id": "trigger_step",
      "name": "Incoming Ticket",
      "step_type": "trigger",
      "config": {"trigger_event": "ticket.created"},
      "next_step_ids": ["retrieval_step"],
      "position": {"x": 100, "y": 100}
    },
    {
      "step_id": "retrieval_step",
      "name": "Knowledge Search",
      "step_type": "knowledge_retrieval",
      "config": {"query_template": "{{trigger.body}}"},
      "next_step_ids": ["agent_step"],
      "position": {"x": 300, "y": 100}
    },
    {
      "step_id": "agent_step",
      "name": "Triage Agent",
      "step_type": "agent",
      "config": {"agent_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"},
      "next_step_ids": [],
      "position": {"x": 500, "y": 100}
    }
  ]
}
```

#### Workflow Execution & Governance (`/api/v1/workflows/...`)
- `POST /api/v1/workflows/{workflow_id}/execute`: Trigger execution of an `active` workflow. Executes DAG steps sequentially or pauses for approval.
- `GET /api/v1/workflows/executions/{execution_id}`: Retrieve execution state, step results, and audit log.
- `POST /api/v1/workflows/executions/{execution_id}/approve`: Grant human approval for execution paused in `waiting_approval`. Resumes execution from approval cursor.
- `POST /api/v1/workflows/executions/{execution_id}/cancel`: Cancel a pending, running, or waiting workflow execution.

#### DAG Validation & Orchestration Architecture
- **Deterministic Entry:** Exactly one `trigger` step root (`in_degree == 0`) required.
- **Graph Integrity:** Cycle detection via 3-color DFS traversal, self-reference prevention, missing `next_step_ids` rejection, duplicate edge deduplication, and unreachable orphan step detection.
- **Traversal Limits:** Bounded execution (`MAX_WORKFLOW_STEPS = 50`, `MAX_EXECUTION_STEPS = 100`) preventing unbounded loops.
- **Agent Delegation:** When an `agent` step runs, orchestration delegates to the Phase 2F `AgentExecutionService`, generating a linked `AgentExecution` record (`source="workflow_step"`, `source_reference_id=workflow_execution.id`).
- **Human-in-the-Loop:** `approval` steps transition execution to `waiting_approval` with a stored `resume_step_id`. Approving resets status to `running` (never persisting `"approved"`) and resumes traversal.
- **Transactional Safety:** Uses database row-level locking (`with_for_update`) during approval and cancellation transitions.
- **Audit Privacy:** State changes emit `workflow.execution.*` events capturing metadata and metrics while omitting raw prompts or step payloads.

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

All 183 backend unit and API integration tests cover:
- FastAPI router, service, and repository layers for Organizations, Users, Memberships, Knowledge, Assistant, Agents, Executions, Workflows, and LLM Gateway
- Real LLM integration & stateless LLM Gateway (request normalization, token usage tracking, latency logging, mock & OpenAI-compatible providers, safe error translation)
- Domain validation (emails, slugs, valid roles, agent domains, valid statuses, lifecycle state transitions, DAG cycle/orphan/edge validation)
- Conflict detection (duplicate slugs, duplicate emails, duplicate org memberships)
- Entity not found handling (404 response codes)
- Strict cross-organization access control & tenant isolation
- CASCADE & preservation behavior on deletion

---

## Database Architecture (15 Tables)

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
| `agent_executions` | UUID | `organization_id` (FK CASCADE), `agent_id` (FK CASCADE), status CHECK, source CHECK |
| `workflows` | UUID | `organization_id` (FK CASCADE), `created_by_user_id` (FK RESTRICT) |
| `workflow_steps` | UUID | `workflow_id` (FK CASCADE), `config` (JSONB), `next_step_ids` (JSONB) |
| `workflow_executions` | UUID | `workflow_id` (FK CASCADE), `execution_log` (JSONB) |
| `audit_logs` | UUID | `organization_id` (FK CASCADE), `actor_id` (FK SET NULL), `details` (JSONB) |

