# MERA - Full Setup Guide for Partner

> Share this with your teammate so they can set up MERA on their own machine.

## Prerequisites (Install These First)

| Tool | Why | Download |
|------|-----|----------|
| **Python 3.11+** | Run agents locally | https://python.org |
| **Docker Desktop** | Run SigNoz + MCP | https://docker.com |
| **Ollama** | Local LLM (free, no API key) | https://ollama.com |
| **Git** | Clone the repo | https://git-scm.com |

## Step 1 — Clone the Repo

```bash
git clone <your-repo-url>
cd Signoz_Agent/Track_3
```

## Step 2 — Pull the LLM Model

Open **Ollama** (it runs in system tray), then:

```bash
ollama pull llama3.2:3b
```

Verify it's running:
```bash
ollama list
# should show llama3.2:3b
```

## Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 4 — Configure Environment

The `.env` file is already set up for local dev. Check it:

```bash
type .env
```

It should contain:
```
OLLAMA_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:3b
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=mera-main-agent
SIGNOZ_MCP_URL=http://localhost:8000/mcp
```

## Step 5 — Install Foundry CLI (for SigNoz deployment)

```powershell
# Windows PowerShell
$ARCH = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
Invoke-WebRequest -Uri "https://github.com/SigNoz/foundry/releases/download/v0.2.11/foundry_windows_${ARCH}.tar.gz" -OutFile foundry.tar.gz -UseBasicParsing
tar -xzf foundry.tar.gz
mkdir -p "$HOME\.local\bin"
mv foundry_windows_*/bin/foundryctl.exe "$HOME\.local\bin\"
$env:Path += ";$HOME\.local\bin"
foundryctl version
# Should show v0.2.11
```

## Step 6 — Start Docker Desktop

Launch **Docker Desktop** from Start Menu. Wait for the whale icon in system tray to stop animating (may take 2-3 min on first run).

Verify:
```powershell
docker ps
# Should show no errors (empty list is fine)
```

## Step 7 — Deploy SigNoz + MCP

```powershell
cd Track_3
foundryctl cast -f casting.yaml
```

This downloads images (~3GB first time, takes 5-10 min) and starts 7 containers.

Verify:
```powershell
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected output (all should show `Up` + `healthy`):
```
mera-signoz-0                             Up ... (healthy)
mera-ingester-1                           Up ...
mera-mcp                                  Up ... (healthy)
mera-metastore-postgres-0                 Up ... (healthy)
mera-telemetrykeeper-clickhousekeeper-0   Up ... (healthy)
mera-telemetrystore-clickhouse-0-0        Up ... (healthy)
mera-telemetrystore-migrator              Up ...
```

## Step 8 — Run the Demo

In a **new terminal** (keep Docker running):

```powershell
cd Track_3
python run.py
```

You'll see 3 self-healing cycles execute. Takes ~2 min.

## Step 9 — View in SigNoz

Open http://localhost:8080 in browser.
- Complete the first-time signup (email + password)
- Go to **Dashboards** → **Import Dashboard** → select `dashboards/mera_dashboard.json`
- Go to **Traces** to see spans from the demo

## Step 10 — Run Tests

```powershell
cd Track_3
python -m pytest tests/ -v
```

All 5 should pass.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `foundryctl: command not found` | Add `$HOME\.local\bin` to PATH or restart terminal |
| Docker containers not starting | Restart Docker Desktop, wait 2 min, retry Step 7 |
| `python` not found | Use `python3` or install Python 3.11+ |
| Ollama connection error | Open Ollama from Start Menu, wait for icon in system tray |
| Port 8080 in use | Run `netstat -ano \| findstr :8080` and kill the process |
| OTel export errors | Those are normal if SigNoz isn't ready yet. Wait and retry |

## Recording the Demo Video (2 min)

Record your screen showing:
1. **0:00** — `docker ps` showing 7 containers
2. **0:20** — `python run.py` executing 3 cycles
3. **1:00** — SigNoz UI at localhost:8080 showing traces
4. **1:30** — Import dashboard from `dashboards/mera_dashboard.json`
5. **1:50** — Dashboard panels rendering with data

## Files to Submit

- `casting.yaml` — Foundry deployment config
- `casting.yaml.lock` — Foundry lock file
- All code in `main_agent/`, `mirror_agent/`, `run.py`
- `dashboards/mera_dashboard.json`
- `MERA_Report.pdf`
- Demo video (2 min)

---

**Team Enthusiast** — KPGU, Vadodara
