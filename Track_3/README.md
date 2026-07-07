# MERA - Mirror Entity Recursive Agent

> **Track:** 03 - Build Your Own | **Team:** Team Enthusiast
> **University:** Dr. Kiran & Pallavi Patel Global University, Vadodara

---

## What is MERA?

A **self-healing AI agent** that:
1. Does useful work (code review) with full OpenTelemetry instrumentation
2. Reads its own traces via SigNoz MCP
3. Detects anomalies (high latency, low confidence, suspicious behavior)
4. Generates fixes automatically
5. Creates SigNoz dashboards + alerts

## SigNoz Features Used

Traces | Metrics | Logs | Dashboards | Alerts | MCP Server

## Architecture

```
Main Agent ----OTel----> SigNoz <----MCP---- Mirror Agent
   ^                                              |
   |______________ Auto-Fix ______________________|
```

## Quick Start (local dev, no Docker)

### Prerequisites
- Python 3.11+
- Ollama running on localhost:11434 with `llama3.2:3b` pulled

### Run
```bash
pip install -r requirements.txt
python run.py
```

Open http://localhost:9000 for the MERA web dashboard or http://localhost:8080 for SigNoz.

## Deployment Options

### 1. Foundry — Deploy SigNoz + MCP only
```bash
foundryctl cast -f casting.yaml
```

### 2. Docker Compose — Deploy full stack (SigNoz + MCP + MERA agents)
```bash
docker compose -f docker-compose.yml up -d
```

### 3. Hybrid — Foundry SigNoz + local Puppython agents
```bash
foundryctl cast -f casting.yaml          # starts SigNoz + MCP on Docker
pip install -r requirements.txt
python run.py                            # agents run locally, connect to Docker SigNoz
```

## Structure
```
Track_3/
  casting.yaml             # Foundry deployment config (SigNoz + MCP)
  casting.yaml.lock        # Foundry lock file
  docker-compose.yml       # Full stack Docker Compose
  main_agent/agent.py      # PR Reviewer with OTel traces
  mirror_agent/mirror.py   # Observer + auto-healer via MCP
  run.py                   # Orchestrator
  Dockerfile.main          # Main agent container
  Dockerfile.mirror        # Mirror agent container
  signoz_config/           # OpenTelemetry collector config
  dashboards/              # SigNoz dashboard template
  tests/                   # Pytest unit tests
  scripts/                 # Setup + demo scripts
  docs/                    # Architecture
  MERA_Report.pdf          # Project report
```

## Tests
```bash
pytest tests/ -v
```
