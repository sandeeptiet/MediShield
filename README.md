# MediShield AI — Multi-Agent Claims Intake & Triage

Capstone project (Assignment 2) — an agentic, multimodal claims intake & triage platform for a fictional health insurer.

## What it does

Receives scanned/uploaded insurance documents (claim forms, IDs, discharge summaries, prescriptions), routes them through a LangGraph multi-agent pipeline, and emits an **Approve / Reject / Escalate** decision with a full justification trail.

```
Document upload
   ↓
Classifier Agent (vision LLM)
   ↓
KYC Agent ┃ Claims Agent ┃ Policy RAG Agent     (parallel)
   ↓
Fraud Agent
   ↓
Orchestrator Agent → decision + audit log
```

## Stack at a glance

| Layer | Tool |
|---|---|
| LLM (every agent) | Claude Sonnet 4.6 (`anthropic` SDK) |
| OCR for images | EasyOCR |
| OCR for PDFs | Docling |
| Embeddings | Qwen3-Embedding-0.6B (HuggingFace, local) |
| Reranker | BAAI/bge-reranker-v2-m3 (HuggingFace, local) |
| Vector store | Qdrant |
| Fraud anomaly | scikit-learn IsolationForest |
| Tamper detection | OpenCV (ELA) |
| Workflow | LangGraph |
| Backend | FastAPI + SQLAlchemy |
| Database | MySQL 8 |
| Frontend | Next.js 14 + NextAuth (Google OAuth) |
| Observability | LangSmith + structlog + Prometheus |
| Deployment | OpenShift (CRC for local dev) |

See `../capstone_project_assignments/analysis_02_MediShield_AI_final.md` for the full design summary.

## Project layout

```
MediShield_02/
├── backend/                 FastAPI service (all 7 agents + LangGraph)
│   ├── app/
│   │   ├── api/v1/          HTTP endpoints
│   │   ├── core/            security, logging, metrics
│   │   ├── models/          SQLAlchemy models
│   │   ├── schemas/         Pydantic request/response schemas
│   │   └── services/ai/     Agent implementations
│   ├── alembic/             DB migrations
│   ├── Containerfile
│   └── pyproject.toml
├── frontend/                Next.js 14 app
│   ├── app/                 routes (App Router)
│   ├── components/
│   ├── lib/
│   ├── Containerfile
│   └── package.json
├── deploy/openshift/        K8s/OpenShift manifests
├── docker-compose.yaml      local dev orchestration
├── .env.example             template for environment variables
└── README.md
```

## Quick start (local dev)

Pre-requisites: Python 3.12+, Node 20+, Docker / Podman, an Anthropic API key, a Google OAuth client.

```bash
# 1. Copy environment template and fill in values
cp .env.example .env
# (edit .env)

# 2. Bring up MySQL + Qdrant
docker-compose up -d mysql qdrant

# 3. Backend
cd backend
uv venv && source .venv/bin/activate
uv pip install -e .
alembic upgrade head
uvicorn app.main:app --reload

# 4. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:3000`. Sign in with Google (your email must be pre-seeded in the `users` table).

## Build phases

This project is being built in phases. Current status:

- [x] **Phase 1** — Scaffolding (folder structure, configs, stubs, manifests)
- [ ] **Phase 2** — Auth + DB (Google OAuth, user/case/audit_log tables, login UI)
- [ ] **Phase 3** — Core agent infrastructure (LangGraph state, Claude wrapper, base agent)
- [ ] **Phase 4** — Individual agents (Classifier → KYC → Claims → Policy RAG → Fraud → Orchestrator)
- [ ] **Phase 5** — Ingestion API + UI (upload, dashboard, case detail, polling)
- [ ] **Phase 6** — Observability + OpenShift deployment

## License

For educational use as part of the Codebasics AI Engineering Bootcamp capstone.
