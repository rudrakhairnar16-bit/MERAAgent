# SigNoz MCP Server: 41 Tools That Turned My AI Agent Into an Observability Powerhouse

**How I discovered that SigNoz's Model Context Protocol server is the missing link between AI agents and observability — and built a self-healing system that fixes itself.**

---

## The Problem: AI Agents Are Flying Blind

Every AI agent I've built has the same blind spot: **it can see the user's code, but it can't see itself.**

I built a PR review agent powered by Llama 3.2 via Ollama. It reviewed code, found bugs, and suggested fixes. But when it started getting slower, returning low-confidence results, and sometimes crashing entirely, I had no way to ask *why*.

Traditional debugging doesn't work for AI agents because:

1. **They're asynchronous** — LLM calls take seconds, not milliseconds
2. **They're probabilistic** — same input can produce different outputs
3. **They compose unpredictably** — five working components can fail together

I needed observability. That's when I found SigNoz's MCP Server, and everything changed.

---

## What Is the SigNoz MCP Server?

MCP stands for **Model Context Protocol** — a JSON-RPC API that exposes SigNoz's entire observability platform as **41 callable tools**.

Think of it as a remote control for your observability data. Instead of clicking through dashboards, you write code:

```python
# Before MCP: Manual UI navigation
# After MCP: One API call
response = requests.post("http://localhost:8000/mcp", json={
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "signoz_search_traces", "arguments": {"limit": 10}},
    "id": 1
}, headers={"SIGNOZ-API-KEY": "your-key"})
```

That's it. Your AI agent can now query its own traces, create dashboards, configure alerts, and analyze logs — all through a single interface.

---

## Deploying SigNoz + MCP in 5 Minutes

I used the **Foundry CLI** — SigNoz's one-command deployment tool:

```bash
foundryctl cast -f casting.yaml
```

This spun up 7 containers:

| Container | Role |
|-----------|------|
| SigNoz UI | Web interface at http://localhost:8080 |
| Query Service | API backend |
| Ingester | Data ingestion pipeline |
| MCP Server | **The star — port 8000** |
| ClickHouse (×2) | Columnar storage for traces |
| Postgres | Metadata store |

> **Note:** The MCP server is included automatically with Foundry. No separate installation needed.

### Authentication

Every MCP call requires a `SIGNOZ-API-KEY` header. Generate one in SigNoz UI (`Settings → API Keys`), or automate it:

```python
# scripts/setup_api_key.py
import requests, json, os

SIGNOZ_DB_URL = "http://localhost:8080/api/v1/..."
payload = {"name": "mera-agent", "role": "ADMIN"}
response = requests.post(SIGNOZ_DB_URL, json=payload,
    headers={"Authorization": "Bearer your-admin-token"})
api_key = response.json()["data"]["apiKey"]
print(f"Your API key: {api_key}")
```

---

## The 41 Tools: A Complete Breakdown

I called `tools/list` and got every tool SigNoz exposes. Here they are, grouped by category:

### 🔍 Traces (7 tools)

The most powerful category. Your agent can search, analyze, and debug traces programmatically:

| Tool | What It Does |
|------|-------------|
| `signoz_search_traces` | Search traces with filters (service, status, duration) |
| `signoz_get_trace_details` | Full span hierarchy for any trace ID |
| `signoz_aggregate_traces` | p50/p95/p99 latency, error rate, call count |
| `signoz_get_trace_tags` | Discover all tag keys across your traces |
| `signoz_span_details` | Get individual span attributes |
| `signoz_compare_traces` | Compare two time ranges side-by-side |
| `signoz_top_endpoints` | Find your slowest and most-called endpoints |

**Real example — finding slow traces:**

```python
def find_slow_traces(mcp_url, api_key, threshold_ms=5000):
    """Ask MCP for traces slower than threshold."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "signoz_search_traces",
            "arguments": {
                "limit": 10,
                "order": "desc",
                "filters": [
                    {"key": "duration", "op": ">", "value": threshold_ms}
                ]
            }
        },
        "id": 1
    }
    r = requests.post(mcp_url, json=payload,
        headers={"SIGNOZ-API-KEY": api_key, "Content-Type": "application/json"})
    return r.json().get("result", [])

# Get your 10 slowest traces
slow = find_slow_traces("http://localhost:8000/mcp", api_key, 5000)
for trace in slow[:3]:
    print(f"Trace: {trace['traceId']} | Duration: {trace['duration']}ms")
```

### 📊 Dashboards (5 tools)

This is where MCP becomes automation gold. You can create, update, and delete dashboards entirely through code:

| Tool | What It Does |
|------|-------------|
| `signoz_list_dashboards` | List all dashboards with metadata |
| `signoz_get_dashboard` | Get full dashboard JSON by ID |
| `signoz_create_dashboard` | **Create a dashboard programmatically** |
| `signoz_update_dashboard` | Update an existing dashboard |
| `signoz_delete_dashboard` | Delete a dashboard |

**Real example — creating a dashboard from code:**

```python
def create_latency_dashboard(mcp_url, api_key):
    """Create a latency monitoring dashboard via MCP."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "signoz_create_dashboard",
            "arguments": {
                "title": "AI Agent Latency Monitor",
                "variables": [{"name": "service", "type": "query", "query": "services()"}],
                "panels": [
                    {
                        "title": "P95 Latency by Service",
                        "query": "p95(duration) by service_name",
                        "type": "timeseries",
                        "y_axis": {"unit": "ms"}
                    },
                    {
                        "title": "Error Rate",
                        "query": "count(status=ERROR) / count(*) * 100",
                        "type": "timeseries",
                        "y_axis": {"unit": "%"}
                    }
                ]
            }
        },
        "id": 1
    }
    r = requests.post(mcp_url, json=payload,
        headers={"SIGNOZ-API-KEY": api_key, "Content-Type": "application/json"})
    return r.json()

dashboard = create_latency_dashboard("http://localhost:8000/mcp", api_key)
print(f"Dashboard created: {dashboard['result']['id']}")
```

This single function can be called by your AI agent every time it deploys a new version — **self-service dashboards, zero clicks**.

### 🚨 Alerts (5 tools)

Your agent can configure its own alert rules:

| Tool | What It Does |
|------|-------------|
| `signoz_list_alerts` | List all alert rules |
| `signoz_get_alert` | Get alert details by ID |
| `signoz_create_alert` | **Create a new alert rule** |
| `signoz_update_alert` | Update an existing alert |
| `signoz_delete_alert` | Delete an alert rule |

### 📝 Logs (3 tools)

| Tool | What It Does |
|------|-------------|
| `signoz_search_logs` | Search logs with Query Builder expressions |
| `signoz_get_log_fields` | Discover available log field names |
| `signoz_aggregate_logs` | Aggregate log data over time |

### 🔧 Services (4 tools)

| Tool | What It Does |
|------|-------------|
| `signoz_list_services` | List all instrumented services |
| `signoz_get_service_top_operations` | Top operations for a service |
| `signoz_get_service_db_metrics` | Database-level metrics |
| `signoz_get_service_external_metrics` | External call metrics |

### 📈 Metrics (6 tools)

Heavyweight analytics for power users:

| Tool | What It Does |
|------|-------------|
| `signoz_get_metric_metadata` | Get metric metadata and schema |
| `signoz_query_metric` | Run ad-hoc metric queries |
| `signoz_get_top_metrics` | Top metrics by ingestion volume |
| `signoz_list_metric_series` | List time series for a metric |
| `signoz_get_metric_timeseries` | Get time series data points |
| `signoz_compare_metrics` | Compare metrics across time ranges |

### 🔐 API Keys & Access (3 tools)

| Tool | What It Does |
|------|-------------|
| `signoz_list_api_keys` | List all API keys |
| `signoz_create_api_key` | Create a new API key |
| `signoz_revoke_api_key` | Revoke an existing API key |

### 🧩 Other Useful Tools (8 tools)

| Tool | What It Does |
|------|-------------|
| `signoz_get_health` | Check MCP server health |
| `signoz_ping` | Ping test |
| `signoz_get_version` | Get SigNoz version |
| `signoz_list_teams` | List teams |
| `signoz_list_members` | List team members |
| `signoz_search_issues` | Search for known issues |
| `signoz_get_usage_stats` | Platform usage statistics |
| `signoz_export_data` | Export trace/metric data |

---

## The Recursive Loop: When Your Agent Observes Itself

Here's where it gets interesting. I built **MERA (Mirror Entity Recursive Agent)** — an agent that uses MCP to observe its own behavior and fix itself.

The loop works like this:

```
┌─────────────────┐        ┌──────────────────┐        ┌───────────────┐
│   Main Agent    │──OTel──▶│     SigNoz       │◀──MCP──│  Mirror Agent │
│  (PR Reviewer)  │        │  (Traces + MCP)   │        │ (Observer)    │
└─────────────────┘        └──────────────────┘        └───────┬───────┘
      ▲                                                        │
      └─────────────────── Auto-Fix ───────────────────────────┘
```

**Step 1:** The Main Agent reviews code and emits OpenTelemetry traces to SigNoz.

**Step 2:** The Mirror Agent queries SigNoz MCP to find anomalies:

```python
def check_my_health(mcp_url, api_key):
    """Mirror Agent: Query my own traces to detect problems."""
    traces = find_slow_traces(mcp_url, api_key, 5000)
    anomalies = []

    for trace in traces:
        # Check for high latency
        if trace['duration'] > 10000:
            anomalies.append({
                "type": "high_latency",
                "severity": "critical",
                "value_ms": trace['duration'],
                "trace_id": trace['traceId']
            })

        # Check for low confidence in reviews
        for span in trace.get('spans', []):
            if span.get('attributes', {}).get('llm.low_confidence') == 'true':
                anomalies.append({
                    "type": "low_confidence",
                    "severity": "warning",
                    "trace_id": trace['traceId'],
                    "span_id": span['spanId']
                })

    return anomalies

issues = check_my_health("http://localhost:8000/mcp", api_key)
print(f"Found {len(issues)} anomalies in my own behavior!")
```

**Step 3:** For each anomaly, the Mirror Agent generates and executes a fix:

| Anomaly | Detection | Auto-Fix |
|---------|-----------|----------|
| High latency | Duration > 5000ms | Reduce LLM max_tokens, lower temperature |
| Low confidence | Confidence < 0.3 | Increase temperature, retry with fallback |
| Zero issues | 0 issues on 500+ char code | Flag for manual review |
| Service down | Connection refused | Docker restart via subprocess |

---

## What I Learned Building With MCP

### 1. The Stateless Design Is a Feature, Not a Bug

Every MCP call is independent. No sessions, no cookies, no state to manage. This makes it trivial for AI agents — they can fire-and-forget without worrying about connection pools or stale contexts.

### 2. Authentication Is Everything

Every single call needs the `SIGNOZ-API-KEY` header. My debugging nemesis was the 401 I kept getting because I forgot the header. **Pro tip:** Set it once in a session object:

```python
import requests

session = requests.Session()
session.headers.update({
    "SIGNOZ-API-KEY": api_key,
    "Content-Type": "application/json"
})

# Now all calls include auth automatically
r = session.post("http://localhost:8000/mcp", json=payload)
```

### 3. Tool Names Follow a Beautiful Pattern

`signoz_<noun>_<verb>` — predictable and self-documenting:

```
signoz_search_traces     → Search + Traces
signoz_create_dashboard  → Create + Dashboard
signoz_list_services     → List + Services
```

An AI agent can discover and understand these tools without a manual.

### 4. Pagination Exists (But It's Sensible)

List endpoints accept `limit` (default 20) and `offset` parameters. For production agents, always implement pagination:

```python
def list_all_dashboards(mcp_url, api_key):
    all_dashboards = []
    offset = 0
    while True:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "signoz_list_dashboards",
                "arguments": {"limit": 50, "offset": offset}
            },
            "id": 1
        }
        r = requests.post(mcp_url, json=payload,
            headers={"SIGNOZ-API-KEY": api_key})
        results = r.json().get("result", [])
        if not results:
            break
        all_dashboards.extend(results)
        offset += len(results)
    return all_dashboards
```

---

## The Full Toolkit: A Python Client for All 41 Tools

I packaged everything into a reusable client. Here's the core:

```python
class SigNozMCPClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = f"{base_url}/mcp"
        self.session = requests.Session()
        self.session.headers.update({
            "SIGNOZ-API-KEY": api_key,
            "Content-Type": "application/json"
        })
        self._req_id = 0

    def _call(self, method: str, params: dict = None) -> dict:
        self._req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._req_id
        }
        r = self.session.post(self.base_url, json=payload, timeout=10)
        r.raise_for_status()
        return r.json().get("result", {})

    def list_tools(self) -> list:
        return self._call("tools/list").get("tools", [])

    def search_traces(self, filters: list = None, limit: int = 20):
        return self._call("tools/call", {
            "name": "signoz_search_traces",
            "arguments": {"limit": limit, "filters": filters or []}
        })

    def create_dashboard(self, title: str, panels: list):
        return self._call("tools/call", {
            "name": "signoz_create_dashboard",
            "arguments": {"title": title, "panels": panels}
        })

    def list_alerts(self):
        return self._call("tools/call", {
            "name": "signoz_list_alerts",
            "arguments": {}
        })

    def get_services(self):
        return self._call("tools/call", {
            "name": "signoz_list_services",
            "arguments": {}
        })

# Usage
client = SigNozMCPClient("http://localhost:8000", api_key)
print(f"Connected! {len(client.list_tools())} tools available")
```

---

## Why This Changes Everything for AI Agents

Before MCP, connecting an AI agent to SigNoz meant:

1. Building a custom API client
2. Reverse-engineering SigNoz's internal endpoints
3. Handling auth, pagination, and error states manually

With MCP:
- **41 tools** ready to use
- **Standard JSON-RPC** interface
- **No UI dependency** — every action is automatable
- **Agent-native** — designed for programmatic access

The result? My MERA agent now:

- Detects when it's running slow (via trace duration)
- Creates its own SigNoz dashboards (via MCP dashboard tools)
- Configures alert rules for itself (via MCP alert tools)
- Applies auto-fixes without human intervention

---

## Try It Yourself in 4 Steps

1. **Deploy SigNoz + MCP**
   ```bash
   foundryctl cast -f casting.yaml
   ```

2. **Get your API key**
   Open http://localhost:8080 → Settings → API Keys → Create Key

3. **List all 41 tools**
   ```python
   import requests
   r = requests.post("http://localhost:8000/mcp", json={
       "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1
   }, headers={"SIGNOZ-API-KEY": api_key})
   print(f"Found {len(r.json()['result']['tools'])} tools")
   ```

4. **Query your first trace**
   ```python
   r = requests.post("http://localhost:8000/mcp", json={
       "jsonrpc": "2.0", "method": "tools/call",
       "params": {"name": "signoz_list_services", "arguments": {}},
       "id": 2
   }, headers={"SIGNOZ-API-KEY": api_key})
   print(r.json())
   ```

---

## What's Next

I'm taking MERA into the **Agents of SigNoz Hackathon** (July 20-26) — a self-healing AI agent that uses SigNoz MCP to observe and fix itself in real-time.

The full project is open-source: [github.com/rudrakhairnar16-bit/MERAAgent](https://github.com/rudrakhairnar16-bit/MERAAgent)

If you're building AI agents, try this:

1. Deploy SigNoz with Foundry
2. Instrument your agent with OpenTelemetry
3. Connect your agent to MCP
4. Watch it discover its own blind spots

Your agent deserves to see itself. SigNoz MCP gives it eyes.

---

*Built with SigNoz EE, Foundry CLI v0.2.11, Ollama + Llama 3.2 3B, and Python 3.11.*

*Follow my work: [@rudrakhaire_](https://x.com/rudrakhaire_) on X*

*#AgentsOfSigNoz #OpenTelemetry #MCP #SelfHealingAI #Observability*
