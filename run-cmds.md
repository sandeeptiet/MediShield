# MediShield — Run & Verify Commands

A running cheat sheet of every command needed to verify each build phase locally.
Run from the project root (`MediShield_02/`) unless noted.

---

## Synthetic test data — generate the dataset

The capstone ships a set of Python generators (not the data itself) in
`Assignment2_datagen_scripts.zip` in the specs folder. They produce:

- 2 policy PDFs (Gold + Silver plans) — for ingestion into Qdrant
- 151 PNGs (claim forms, IDs, prescriptions, discharge summaries, policy amendments)
- 4 out-of-distribution PNGs
- `metadata.json` with ground-truth labels (fraud flags, `expected_decision`, edge cases)

### 1. Unzip the generators

```bash
cd /Users/sandeepkapoor/Desktop/prep/capstone_project_assignments
unzip Assignment2_datagen_scripts.zip -d MediShield_data_gen
```

### 2. Install generator dependencies (one-time)

```bash
pip install pillow reportlab faker
# If a generator complains about a missing module on first run, pip-install it and retry.
```

### 3. Run the four generators in order

```bash
cd MediShield_data_gen/scripts/scripts
python generate_docs.py            # 151 PNGs + metadata.json
python generate_gold_policy.py     # Gold plan PDF
python generate_silver_policy.py   # Silver plan PDF
python generate_unknown.py         # 4 OOD PNGs (appends to metadata.json)
# Output lands in ./dataset/
```

### 4. Move the dataset into the project

```bash
mv dataset /Users/sandeepkapoor/Desktop/prep/MediShield_02/sample_data
```

Final layout:

```
MediShield_02/
├── sample_data/
│   ├── policies/                    ← ingest these PDFs into Qdrant
│   │   ├── medishield_gold_plan.pdf
│   │   └── medishield_silver_plan.pdf
│   ├── claim_forms/                 ← upload these PNGs through the UI
│   ├── discharge_summaries/
│   ├── id_documents/
│   ├── prescriptions/
│   ├── policy_amendments/
│   ├── unknown/
│   └── metadata.json                ← ground truth for evaluation
```

### 5. Ingest the policy PDFs into Qdrant

```bash
cd /Users/sandeepkapoor/Desktop/prep/MediShield_02
docker-compose up -d qdrant        # if not already running

cd backend
source .venv/bin/activate
python -m scripts.ingest_policies ../sample_data/policies/
```

You can now use any PNG from `sample_data/<category>/` as an upload to test
the pipeline. For a quick smoke test, one claim form + one ID document is
enough — the full 155 are only needed if you want to score Decision
Correctness against `metadata.json`.

---

## Phase 4 — Verify the real agents

### 0. One-time setup

```bash
# Move into the project
cd /Users/sandeepkapoor/Desktop/prep/MediShield_02

# Copy environment template
cp .env.example .env
# Edit .env and set at minimum: ANTHROPIC_API_KEY
# (Google OAuth and LangSmith keys are optional for Phase 4 tests since tests mock everything)
```

### 1. Create backend virtual env and install dependencies

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 2. Run the unit-test suite (no external services needed)

All Phase 4 unit tests mock Claude, Qdrant, and embeddings — they do NOT require
MySQL, Qdrant, or an Anthropic API key to be live.

```bash
# Run everything
pytest tests/ -v

# Or run each file separately
pytest tests/test_graph_compiles.py -v
pytest tests/test_agents.py -v
```

**Expected:** 13 tests pass (3 graph shape + 10 agent contracts).

### 3. (Optional) Run the agentic-RAG path against a live Qdrant

This exercises the **real** Qwen3 embedder + BGE reranker + Qdrant +
Docling — no mocks. Requires an Anthropic key.

```bash
# 3a. Start Qdrant locally
cd ..                                    # back to project root
docker-compose up -d qdrant

# 3b. Place sample policy PDFs anywhere — e.g. ../sample_policies/
mkdir -p ../sample_policies
# Drop your PDFs into ../sample_policies/

# 3c. Ingest them into Qdrant (Docling parse → Qwen3 embed → upsert)
cd backend
source .venv/bin/activate
python -m scripts.ingest_policies ../sample_policies/
# First run pulls Qwen3-Embedding-0.6B (~1.2 GB) from HuggingFace — be patient.

# 3d. Sanity-check the collection exists and has points
curl -s http://localhost:6333/collections/policy_chunks | python -m json.tool

# 3e. Trigger a quick end-to-end Python smoke run (requires ANTHROPIC_API_KEY set)
python - <<'PY'
from app.services.ai.orchestrator import run_pipeline
out = run_pipeline(
    case_id="live-smoke-1",
    document_path="../sample_policies/your_sample_claim_image.jpg",  # adjust
    uploaded_by=1,
)
print("Decision:", out.get("decision"))
print("Justification:", out.get("justification"))
PY
```

### 4. Run ELA tamper detection in isolation (no Claude needed)

```bash
cd backend
source .venv/bin/activate
python - <<'PY'
from app.services.ai.tamper_detection import compute_ela
result = compute_ela("path/to/your/image.jpg")
print(result)
PY
```

### 5. Quick lint / typecheck (optional)

```bash
ruff check app/
# mypy app/   # opt-in if you've added stricter typing
```

---

---

## Phase 5 — End-to-end run with the UI

### 1. Bring up the infra and the backend

```bash
cd /Users/sandeepkapoor/Desktop/prep/MediShield_02
docker-compose up -d mysql qdrant

cd backend
source .venv/bin/activate
alembic upgrade head        # creates users/cases/ai_audit_logs tables
python -m scripts.seed_users  # add your Gmail to USERS first
uvicorn app.main:app --reload
```

### 2. Start the frontend

```bash
# in a separate terminal
cd /Users/sandeepkapoor/Desktop/prep/MediShield_02/frontend
npm install
npm run dev
```

Open http://localhost:3000 and sign in with Google.

### 3. Exercise the upload + polling flow

1. From `/dashboard`, click the file picker and pick an image (claim form / ID / etc.).
2. The case appears in the table with status `RECEIVED → PROCESSING → DECIDED`.
3. Click the case ID to open `/cases/<id>` and view per-agent outputs.
4. If signed in as an ADMIN, an override form appears on `DECIDED` cases.

### 4. Hit the API directly with curl

```bash
# Get a session token from NextAuth (open http://localhost:3000/api/auth/session in the browser
# while signed in, copy the `medishieldJwt` value).
TOKEN="<paste medishieldJwt>"

# Upload
curl -X POST http://localhost:8000/api/v1/cases/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.jpg"

# List
curl -s http://localhost:8000/api/v1/cases \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Detail
curl -s http://localhost:8000/api/v1/cases/<case_id> \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### 5. Verify audit + metrics

```bash
# In MySQL
docker-compose exec mysql mysql -u medishield -pdev medishield \
  -e "SELECT action, status, COUNT(*) FROM ai_audit_logs GROUP BY action, status;"

# Prometheus metrics
curl -s http://localhost:8000/metrics | grep medishield_cases_total
```

---

## Phase 6 — Deploy to CRC (OpenShift Local)

### 0. CRC prerequisites (one-time)

```bash
# Bump CRC resources for the model load
crc config set memory 12288       # 12 Gi
crc config set cpus 6
crc config set disk-size 60
crc setup
crc start

# Authenticate the local oc client
eval $(crc oc-env)
oc login -u developer https://api.crc.testing:6443       # password: developer
```

### 1. Make sure `.env` has real values

```bash
cd /Users/sandeepkapoor/Desktop/prep/MediShield_02
# Required: ANTHROPIC_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
# JWT_SECRET, NEXTAUTH_SECRET, MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD
# (LANGSMITH_API_KEY optional)
$EDITOR .env
```

For Google OAuth, add an additional Authorized redirect URI in Google Cloud Console:

    https://frontend-medishield.apps-crc.testing/api/auth/callback/google

### 2. Run the deploy script

```bash
./deploy/openshift/deploy.sh
```

It will:

1. Create the `medishield` project if missing
2. Create / refresh `medishield-secrets` from `.env`
3. Build the backend image with `oc start-build` (binary build from `./backend`)
4. Build the frontend image (binary build from `./frontend`)
5. Apply all manifests (`00-namespace`, `11-configmap`, `20-mysql`, `22-qdrant`, `30-backend`, `31-frontend`)
6. Wait for all four Deployments to roll out
7. Print the routes
8. Run `scripts/seed_users` inside the backend pod

### 3. Visit the app

```bash
oc get route frontend -o jsonpath='{.spec.host}'
# Open https://<that-host> in your browser
```

Sign in with Google. The Google account you use must already be in the
seeded `users` table (edit `backend/scripts/seed_users.py` and re-run the
script if you need to add yourself).

### 4. Quick OpenShift health checks

```bash
# All pods running?
oc get pods

# Tail backend logs
oc logs deployment/backend -f

# Latest 50 audit rows
oc exec deployment/mysql -- mysql -u medishield -p"$MYSQL_PASSWORD" medishield \
  -e "SELECT action, status, COUNT(*) FROM ai_audit_logs GROUP BY action, status;"

# Prometheus metrics inside the cluster
oc exec deployment/backend -- curl -s http://localhost:8000/metrics | \
  grep -E 'medishield_(cases|http|agent)' | head -40

# Hit /readyz from outside the cluster
BACKEND_HOST=$(oc get route backend -o jsonpath='{.spec.host}')
curl -sk "https://$BACKEND_HOST/readyz" | python -m json.tool
```

### 5. Tear down

```bash
oc delete project medishield
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: app` | Run pytest / scripts from `backend/` with the venv activated, not from project root. |
| Qdrant 404 on collection | The ingest script auto-creates the collection. Re-run `python -m scripts.ingest_policies …`. |
| Slow first model load | Qwen3 + BGE pull ~2 GB total from HuggingFace on first call. Subsequent runs use the local cache. |
| `ANTHROPIC_API_KEY` missing during live run | `export ANTHROPIC_API_KEY=...` in the shell, or set it in `.env` (root). The unit tests do NOT need this — they mock Claude. |
| Pytest can't find `email-validator` | `uv pip install -e ".[dev]"` again — Phase 4 added it to `pyproject.toml`. |


 All six phases complete

  [x] Phase 1 — Scaffolding
  [x] Phase 2 — Auth + DB
  [x] Phase 3 — Core agent infrastructure
  [x] Phase 4 — Real agents
  [x] Phase 5 — Ingestion API + UI
  [x] Phase 6 — Observability + deployment

  The application is now end-to-end functional: sign in with Google → upload a document → 7-agent LangGraph pipeline runs in the
  background → polling UI shows status → final decision with per-agent justification → ADMIN can override → full audit trail in MySQL →
  Prometheus metrics on /metrics → ServiceMonitor scraped by OpenShift → LangSmith traces if the API key is set.

  What would you like to do next? Some natural follow-ups:
  - Smoke-test the local docker-compose path end-to-end before deploying to CRC
  - Generate synthetic test documents (the brief asks for 20 with ground-truth labels for evaluation)
  - Add a small eval harness that scores Decision Correctness against ground truth
  - Polish the README with a demo GIF placeholder and architecture diagram
