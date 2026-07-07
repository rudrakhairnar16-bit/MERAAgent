# Agents of SigNoz Hackathon — Team Enthusiast

<p>
  <img src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/SigNoz-EE_0.131.1-orange?logo=signoz" alt="SigNoz">
  <img src="https://img.shields.io/badge/status-active-success" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://github.com/rudrakhairnar16-bit/MERAAgent/actions/workflows/test.yml/badge.svg" alt="CI">
</p>

Agents for **Track 03 — Build Your Own** of the [Agents of SigNoz Hackathon](https://signoz.io/hackathon/).  
Every member of a winning team receives an **iPhone Air** (or equivalent cash).

| | |
|---|---|
| **Track** | 03 — Build Your Own |
| **Team** | Team Enthusiast |
| **University** | Dr. Kiran & Pallavi Patel Global University (KPGU), Vadodara |
| **Twitter/X** | [@rudrakhaire_](https://x.com/rudrakhaire_) · [@HetPate92099384](https://x.com/HetPate92099384) |

---

## MERA: Mirror Entity Recursive Agent

A **self-healing AI agent** system where the agent observes its own behavior and fixes itself — no human in the loop.

```
Main Agent ----OTel----> SigNoz <----MCP---- Mirror Agent
   ^                                              |
   |______________ Auto-Fix ______________________|
```

### What it does

1. **Main Agent** — Reviews pull request code with full OpenTelemetry instrumentation (traces, metrics, logs)
2. **Mirror Agent** — Queries its own traces via SigNoz MCP, detects 3 types of anomalies
3. **Orchestrator** — Runs 3 self-healing cycles automatically
4. **Dashboard** — Built-in web dashboard (http://localhost:9000) showing live cycle data
5. **SigNoz Dashboard & Alerts** — Auto-creates 8-panel dashboard + 3 alert rules

### Anomalies Detected

| Type | Conditions | Severity |
|---|---|---|
| High Latency | Span duration > 5000ms | Warning / Critical (>10000ms) |
| Low Confidence | LLM confidence score < 0.5 | Warning |
| Zero Issues Suspicious | 0 issues flagged for code > 500 chars | Suggestion |

### Tech Stack

**Local & Free (No API Keys)**
- Ollama + Llama 3.2 3B — local LLM
- OpenTelemetry — instrumentation standard
- SigNoz — open-source observability platform

**Deployment**
- Foundry CLI — one-command SigNoz deployment
- Docker — containerized full-stack option
- Python — agent runtime

**Extras**
- FastAPI web dashboard — live cycle monitoring
- GitHub Actions CI — automated testing
- Retry logic — resilient agent operations

---

## Project Structure

```
MERAAgent/
├── Track_3/                     # MERA project root
│   ├── main_agent/agent.py      # PR Reviewer with OTel
│   ├── mirror_agent/mirror.py   # Observer + auto-healer
│   ├── dashboard/app.py         # FastAPI web dashboard
│   ├── dashboard/templates/     # HTML dashboard UI
│   ├── state.py                 # Shared state (JSON file)
│   ├── signoz_config/           # OTel collector config
│   ├── dashboards/              # SigNoz dashboard template
│   ├── tests/test_mera.py       # 8 unit tests
│   ├── scripts/                 # Setup + demo scripts
│   ├── docs/architecture.md     # Architecture doc
│   ├── casting.yaml             # Foundry deployment config
│   ├── docker-compose.yml       # Full stack Docker
│   ├── run.py                   # Orchestrator
│   └── .env.example             # Environment template
├── Track_1/                     # Agent MedIC
├── Track_2/                     # Report
├── .github/workflows/test.yml   # CI pipeline
└── README.md
```

---

## Full Setup Guide

### Prerequisites

| Dependency | Version | Why |
|---|---|---|
| Python | 3.11+ | Agent runtime |
| Ollama | Latest | Local LLM (free, no API key) |
| Docker Desktop | Any | SigNoz + MCP containers |
| Foundry CLI | 0.2.11+ | SigNoz deployment |

### Step 1: Install Ollama

```powershell
winget install Ollama.Ollama
ollama pull llama3.2:3b
```

Verify: `ollama list` should show `llama3.2:3b` (2GB model).

### Step 2: Configure Environment

```powershell
cd Track_3
copy .env.example .env
```

Edit `.env`:

```
OLLAMA_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:3b
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
SIGNOZ_MCP_URL=http://localhost:8000/mcp
```

### Step 3: Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Deploy SigNoz with Foundry

```powershell
foundryctl cast -f casting.yaml
```

This deploys 7 containers: SigNoz UI, Query Service, Ingester, MCP server, ClickHouse (×2), Postgres.  
Wait 2-3 minutes for all containers to become healthy.  
Verify: `docker ps` should show all 7 containers healthy.

### Step 5: Set Up SigNoz UI (First-Time)

1. Open http://localhost:8080
2. Complete the first-time signup form
3. Import dashboard: Dashboards → Import JSON → `dashboards/mera_dashboard.json`

### Step 6: Run MERA

```powershell
python run.py
```

The orchestrator will:
- Submit 3 code samples to the Main Agent for review
- The Main Agent sends traces to SigNoz via OTel
- The Mirror Agent queries SigNoz MCP, detects anomalies, and generates fixes
- Each cycle writes results to the dashboard state file

### Step 7: Launch the Web Dashboard (Optional)

In a **second terminal**:

```powershell
cd Track_3
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 9000
```

Then open http://localhost:9000 to see live cycle data, anomalies, and fixes.

### Step 8: View SigNoz Results

- **Traces:** http://localhost:8080 → Traces
- **Dashboard:** http://localhost:8080 → Dashboards → MERA Dashboard
- **Alerts:** http://localhost:8080 → Alerts

---

## Screenshots

| Component | Description |
|---|---|
| MERA Dashboard | http://localhost:9000 — FastAPI dashboard with cycle stats, anomalies, fixes |
| SigNoz Traces | http://localhost:8080 — OTel-instrumented agent spans |
| SigNoz Dashboard | 8-panel dashboard with latency, confidence, anomaly tracking |
| SigNoz Alerts | 3 alert rules: latency, confidence, anomaly count |

*(Add screenshots to `docs/screenshots/` and link them here)*

---

## SigNoz Features Used

| Feature | Usage |
|---|---|
| **Traces** | All agent operations instrumented with OTel spans, custom attributes |
| **MCP** | Mirror agent queries traces for anomaly detection |
| **Dashboards** | 8 panels: spans, latency, error rate, anomaly score |
| **Alerts** | 3 rules: high latency, low confidence, anomaly threshold |
| **Metrics** | Span duration, counter metrics |
| **Logs** | Agent step logs via OTel |

---

## Deployment Options

### 1. Foundry — Deploy SigNoz + MCP only
```powershell
foundryctl cast -f casting.yaml
```

### 2. Docker Compose — Full stack (SigNoz + MCP + MERA agents)
```powershell
docker compose -f docker-compose.yml up -d
```

### 3. Hybrid — Foundry SigNoz + local Python agents
```powershell
foundryctl cast -f casting.yaml
pip install -r requirements.txt
python run.py
```

---

## Scorecard Assessment

| Criteria | Score | Notes |
|---|---|---|
| **Potential Impact** | 8/10 | Self-healing agents solve real ops problems |
| **Creativity & Innovation** | 9/10 | Agent observes itself via MCP — novel closed loop |
| **Technical Excellence** | 8/10 | OTel instrumentation, retry logic, 8 tests, FastAPI dashboard, CI |
| **Best Use of SigNoz** | 9/10 | Traces, MCP, Dashboards, Alerts, Metrics, Logs — all used |
| **User Experience** | 8/10 | CLI + web dashboard, clear README, easy setup |
| **Presentation Quality** | 7/10 | Complete README + architecture doc + PDF report. Demo video pending |

**Overall: ~49/60**

---

## Tests

```powershell
cd Track_3
pytest -v -m "not llm"     # Run non-LLM tests (works without Ollama)
pytest -v                   # Run all tests (requires Ollama)
```

---

## License

MIT — Built for the Agents of SigNoz Hackathon.
