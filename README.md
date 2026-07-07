# Agents of SigNoz Hackathon — Team Enthusiast

Agents for **Track 03 — Build Your Own** of the [Agents of SigNoz Hackathon](https://signoz.io/hackathon/).

| | |
|---|---|
| **Track** | 03 — Build Your Own |
| **Team** | Team Enthusiast |
| **University** | Dr. Kiran & Pallavi Patel Global University (KPGU), Vadodara |
| **Twitter/X** | [@KartikGoluguri](https://x.com/KartikGoluguri) |

---

## Tracks

### Track 3 — MERA: Mirror Entity Recursive Agent

A **self-healing AI agent** system that:

1. **Main Agent** — Reviews pull request code with full OpenTelemetry instrumentation (traces, metrics, logs)
2. **Mirror Agent** — Queries its own traces via SigNoz MCP, detects anomalies (high latency, low confidence, suspicious patterns)
3. **Orchestrator** — Runs 3 self-healing cycles automatically using threaded Python
4. **Dashboard & Alerts** — Auto-creates SigNoz dashboards (8 panels) and alert rules (3 rules)

**Architecture:**
```
Main Agent ----OTel----> SigNoz <----MCP---- Mirror Agent
   ^                                              |
   |______________ Auto-Fix ______________________|
```

**Tech Stack:** Ollama + Llama 3.2 3B (local, free, no API key) | SigNoz (Traces, MCP, Dashboards, Alerts) | Foundry | Docker | OpenTelemetry | Python

### Track 1 — Agent MedIC
Agentic AI for medical insurance classification and prediction.

### Track 2 — (Report)

---

## Full Setup Guide (Track 3 — MERA)

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
3. Import dashboard: go to Dashboards → Import JSON → select `dashboards/mera_dashboard.json`

### Step 6: Run MERA

```powershell
python run.py
```

The orchestrator will:
- Submit 3 code samples to the Main Agent for review
- The Main Agent sends traces to SigNoz via OTel
- The Mirror Agent queries SigNoz MCP, detects anomalies, and generates fixes
- Each cycle prints a clear status message

### Step 7: View Results

- **Traces:** http://localhost:8080 → Traces tab
- **Dashboard:** http://localhost:8080 → Dashboards → MERA Dashboard
- **Alerts:** http://localhost:8080 → Alerts

### Run Tests

```powershell
pytest tests/ -v
```

### Project Structure

```
Track_3/
├── main_agent/
│   └── agent.py              # PR Reviewer with OTel traces
├── mirror_agent/
│   └── mirror.py             # Observer + auto-healer via MCP
├── signoz_config/
│   └── otel-collector-config.yaml
├── dashboards/
│   └── mera_dashboard.json   # 8 panels + 3 alert rules
├── tests/
│   └── test_mera.py          # 5 unit tests
├── scripts/
│   ├── setup.bat
│   └── run_demo.bat
├── docs/
│   └── architecture.md
├── casting.yaml              # Foundry deployment config
├── casting.yaml.lock
├── docker-compose.yml        # Full stack alternative
├── Dockerfile.main
├── Dockerfile.mirror
├── run.py                    # Orchestrator
├── requirements.txt
├── .env.example
├── MERA_Report.pdf
└── README.md
```

## SigNoz Features Used

| Feature | Usage |
|---|---|
| **Traces** | All agent operations instrumented with OTel spans |
| **MCP** | Mirror agent queries traces for anomaly detection |
| **Dashboards** | 8 panels: spans, latency, error rate, anomaly score |
| **Alerts** | 3 rules: high latency, low confidence, anomaly threshold |
| **Metrics** | Span duration, counter metrics |
| **Logs** | Agent step logs via OTel |

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

## License
MIT — Hackathon project.
