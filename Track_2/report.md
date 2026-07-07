# Agents of SigNoz — Track 2: SLO / Error-Budget Dashboard Pack

---

## Team

- **Rudra** — KPGU (Dr. Kiran and Pallavi Patel Global University)
- **Het Patel** — KPGU

---

## Table of Contents

1. [Kyu (Why) — The Problem & Motivation](#1-kyu-why--the-problem--motivation)
2. [Kya (What) — Project Overview](#2-kya-what--project-overview)
3. [Kese (How) — Implementation Plan](#3-kese-how--implementation-plan)
4. [Kab (When) — Timeline & Schedule](#4-kab-when--timeline--schedule)
5. [Konsa Tools (Which Tools & Technologies)](#5-konsa-tools-which-tools--technologies)
6. [Architecture Overview](#6-architecture-overview)
7. [Score Enhancement Breakdown (Judging Criteria)](#7-score-enhancement-breakdown-judging-criteria)
8. [Win Probability Estimate](#8-win-probability-estimate)
9. [Risk Assessment & Mitigation](#9-risk-assessment--mitigation)

---

### Track 2 Prize

> **Apple iPad** (one per team member, or equivalent cash amount)
>
> Maximum team size: 4 → **4 iPads total**
>
> Plus eligibility for AWS credits ($5K/$3K/$2K for top 3 overall)

---

## 1. Kyu (Why) — The Problem & Motivation

### The Problem

AI agents and production services are increasingly becoming **black boxes**. When:

- Latency spikes unexpectedly
- Token costs explode
- An agent hallucinates or fails in production
- A service degrades gradually

...teams are **flying blind**. You cannot debug what you cannot see.

### Why SLOs & Error Budgets?

Service Level Objectives (SLOs) and Error Budgets are the **industry-standard SRE framework** used at Google, Netflix, Amazon, and every serious tech company. They answer one critical question:

> **"Is my service reliable enough, or should I stop shipping features and fix it?"**

An error budget is the amount of unreliability a service can tolerate over a time window. When it's depleted, the team stops feature work and focuses on reliability.

### Why Track 2 (Signals & Dashboards)

| Reason | Detail |
|---|---|
| **Learning value** | Teaches OpenTelemetry (industry standard), SigNoz platform, Query Builder, SRE fundamentals |
| **Portfolio worth** | SLO dashboards are a real-world artifact used in production — impressive to employers |
| **Achievable in 7 days** | Not overly complex; scope is well-defined |
| **Differentiator** | Most teams will chase AI agent projects (Track 1); a polished SRE dashboard stands out |
| **Practicality** | Can be demonstrated live and is immediately understandable to judges |

### Our Core Motivation

> **Winning is secondary. Mastering OpenTelemetry, SigNoz, and SRE observability is the primary goal — skills that pay far more than any hackathon prize.**

---

## 2. Kya (What) — Project Overview

### What We Will Build

A **reusable SLO / Error-Budget Dashboard Pack** that:

1. **Instruments 2+ microservices** with OpenTelemetry (traces + metrics + logs)
2. **Computes SLOs** (latency, error rate, throughput) using SigNoz Query Builder
3. **Visualizes error budget burn rate** in a real-time SigNoz dashboard
4. **Sets up alerts** that fire when error budget depletes too fast
5. **Integrates SigNoz MCP** — an AI agent that answers error budget questions in natural language
6. **Implements auto-remediation** — webhook-based rollback or scale-up when budget is critical

### Key Deliverables

| Deliverable | Description |
|---|---|
| SigNoz deployment via Foundry | `casting.yaml` + `casting.yaml.lock` committed |
| OTel-instrumented demo app | 2+ services with traces, metrics, logs |
| SLO dashboard | Query Builder panels showing SLIs, error budget, burn rate |
| Alert rules | At least 3 alerts (warning, critical, burn rate) |
| MCP AI agent | LangChain agent querying SigNoz MCP |
| Auto-remediation webhook | AWS Lambda / n8n triggered by SigNoz alert |
| GitHub repo | Clean code, README, architecture diagram |
| Demo video | 2-min Loom/YouTube showing full workflow |
| Blog post | Side track submission for LEGO prize |

---

## 3. Kese (How) — Implementation Plan

### Phase 1: SigNoz Setup & Demo App (Day 1-2)

**Objective:** Get SigNoz running and ingesting telemetry.

**Steps:**

1. Install SigNoz using **Foundry** (one-step install with MCP server)
   ```bash
   # Follow: https://signoz.io/docs/install/docker/
   curl -sL https://github.com/SigNoz/foundry/releases/latest/download/install.sh | bash
   foundry deploy
   ```
2. Deploy the **OpenTelemetry demo app** (otel-demo-lite)
   ```bash
   git clone https://github.com/SigNoz/opentelemetry-demo-lite
   cd opentelemetry-demo-lite
   docker-compose up
   ```
3. Verify traces, metrics, and logs appearing in SigNoz UI
4. Commit `casting.yaml` and `casting.yaml.lock` to repo

**Key tools:** Foundry, Docker, SigNoz UI, OTel demo app

**Validation check:** SigNoz dashboard shows live telemetry from demo app.

---

### Phase 2: Multi-Service Instrumentation (Day 3-4)

**Objective:** Manually instrument 2+ custom services for deep telemetry.

**Steps:**

1. Choose 2 services (e.g., Python Flask API + Node.js worker)
2. Add OpenTelemetry SDKs:
   - Python: `opentelemetry-distro`, `opentelemetry-exporter-otlp`
   - Node.js: `@opentelemetry/sdk-node`, `@opentelemetry/exporter-trace-otlp-http`
3. Export telemetry to SigNoz OTLP endpoint:
   ```python
   # Python example
   from opentelemetry import trace
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
   from opentelemetry.sdk.trace import TracerProvider

   provider = TracerProvider()
   exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
   provider.add_span_processor(BatchSpanProcessor(exporter))
   trace.set_tracer_provider(provider)
   ```
4. Add **custom attributes** for SLO tracking (e.g., `service.name`, `slo_tier`)
5. Add **structured logs** correlated with traces (trace_id in log records)
6. Verify **multi-service traces** showing complete request flow across services

**Key tools:** OTel SDKs (Python, Node.js), SigNoz UI trace viewer

**Validation check:** A single request generates a distributed trace spanning both services.

---

### Phase 3: SLO Dashboards & Alerts (Day 5)

**Objective:** Build the core dashboard using SigNoz Query Builder.

**Steps:**

1. **Define SLIs (Service Level Indicators):**
   - **Latency SLI:** p99 latency < 500ms over 5-min window
   - **Error Rate SLI:** error rate < 1% over 5-min window
   - **Throughput SLI:** request rate > 10 req/s

2. **Create Query Builder panels:**
   - Panel 1: p99 latency chart (time series)
   - Panel 2: Error rate % (time series + threshold line)
   - Panel 3: Request rate (time series)
   - Panel 4: **Error budget remaining** (gauge chart, % remaining)
   - Panel 5: **Error budget burn rate** (line chart with warning/critical zones)

3. **Set up 3 SigNoz alerts:**
   - **Alert 1 (Warning):** Error budget < 50% remaining → Slack/PagerDuty
   - **Alert 2 (Critical):** Error budget < 20% remaining → urgent notification
   - **Alert 3 (Burn Rate):** Burn rate > 2x for 10 minutes → webhook to auto-remediation

4. **Add cross-signal correlation:**
   - Link a specific high-latency trace → log context → error budget impact
   - Add a "Trace ID" panel that shows related logs for any selected trace

**Key tools:** SigNoz Query Builder, Dashboards, Alerts, Logs management

**Validation check:** Simulate a failure — dashboard shows error budget burning, alerts fire.

---

### Phase 4: MCP + AI Agent Integration (Day 6)

**Objective:** Add the highest-scoring enhancement — an AI agent powered by SigNoz MCP.

**Steps:**

1. **Set up SigNoz MCP server** (already included in Foundry install)
2. **Build a LangChain agent** that uses SigNoz MCP as a tool:
   ```python
   from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
   from langchain_community.chat_models import ChatOpenAI

   signoz_mcp_tool = Tool(
       name="SigNozErrorBudget",
       func=lambda q: query_signoz_mcp(q),
       description="Query SigNoz error budget, SLO status, and alert info"
   )

   agent = initialize_agent(
       tools=[signoz_mcp_tool],
       llm=ChatOpenAI(model="gpt-4"),
       agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
   )
   ```
3. **Deploy agent as a simple web app** (Flask/Streamlit UI)
4. **Demo scenario:** Show a judge asking the agent "What's our error budget status?"

**Key tools:** SigNoz MCP Server, LangChain, OpenAI/Claude API, Flask/Streamlit

**Validation check:** Agent can answer 3+ distinct questions about live telemetry.

---

### Phase 5: Auto-Remediation Webhook (Day 6 continuous)

**Objective:** Close the loop — alert triggers automated action.

**Steps:**

1. **Create a webhook receiver** (AWS Lambda + API Gateway or n8n workflow)
2. **Configure SigNoz alert** to POST to webhook URL when error budget is critical
3. **Webhook logic:**
   - Option A: `kubectl rollout undo deployment/my-service`
   - Option B: `docker-compose scale my-service=3` (up from 2)
   - Option C: Restart the problematic service
4. **Webhook returns confirmation** — dashboard shows "Auto-remediation triggered" event

**Key tools:** AWS Lambda / n8n, SigNoz Alert webhook, kubectl / docker-compose

**Validation check:** Trigger error budget breach → alert fires → webhook runs → service recovers.

---

### Phase 6: Polish, Demo & Submission (Day 7)

**Objective:** Package everything for maximum judge impact.

**Steps:**

1. **Clean GitHub repo structure:**
   ```
   Signoz-Agent-Project/
   ├── casting.yaml
   ├── casting.yaml.lock
   ├── services/
   │   ├── flask-api/         # Python service with OTel
   │   └── node-worker/       # Node.js service with OTel
   ├── dashboards/
   │   └── slo-dashboard.json  # Exportable dashboard config
   ├── alerts/
   │   └── alert-rules.json    # Alert configurations
   ├── mcp-agent/
   │   └── agent.py            # LangChain + SigNoz MCP agent
   ├── auto-remediation/
   │   └── webhook-handler.py  # Lambda or n8n workflow
   ├── demo/
   │   ├── simulate-failure.sh # Script to generate bad telemetry
   │   └── screenshots/        # Dashboard screenshots
   ├── README.md               # Full documentation
   └── ARCHITECTURE.md         # Architecture diagram + explanation
   ```

2. **Record demo video (2 minutes max):**
   - 0:00-0:30: Show normal state — healthy SLO dashboard
   - 0:30-1:00: Trigger failure — error budget starts burning
   - 1:00-1:20: Alert fires → MCP agent answers "What's happening?"
   - 1:20-1:40: Auto-remediation triggers → service recovers
   - 1:40-2:00: Dashboard shows budget stabilizing — close

3. **Write blog post** for side track:
   - Title: *"Building an Autonomous SLO Dashboard with SigNoz MCP and OpenTelemetry"*
   - Content: Problem → Architecture → Implementation → Demo → Key learnings

4. **Submit on WeMakeDevs platform**

**Key tools:** GitHub, OBS/Loom, markdown, YouTube

---

## 4. Kab (When) — Timeline & Schedule

### Daily Breakdown

| Day | Date | Phase | Tasks | Milestone |
|---|---|---|---|---|
| **Day 1** | Jul 20 (Sun) | Phase 1 | Kickoff livestream (7:30 PM IST), install Foundry, deploy SigNoz, explore UI | SigNoz running |
| **Day 2** | Jul 21 (Mon) | Phase 1 | Deploy OTel demo app, verify telemetry flow, commit casting files | Telemetry flowing |
| **Day 3** | Jul 22 (Tue) | Phase 2 | Instrument Python service with OTel SDK, test traces | 1 service instrumented |
| **Day 4** | Jul 23 (Wed) | Phase 2 | Instrument Node.js worker, verify distributed traces, add logs correlation | Multi-service tracing |
| **Day 5** | Jul 24 (Thu) | Phase 3 | Build Query Builder panels, create SLO dashboard, set up 3 alerts | Dashboard + alerts live |
| **Day 6** | Jul 25 (Fri) | Phase 4+5 | MCP agent integration, auto-remediation webhook, end-to-end testing | Full system working |
| **Day 7** | Jul 26 (Sat) | Phase 6 | Polish README, record demo, write blog, submit | Submission complete |

### Daily Commitment (per person)

| Day | Hours |
|---|---|
| Day 1 | 3-4 hrs |
| Day 2 | 4-5 hrs |
| Day 3 | 5-6 hrs |
| Day 4 | 5-6 hrs |
| Day 5 | 6-7 hrs |
| Day 6 | 6-7 hrs |
| Day 7 | 4-5 hrs |
| **Total** | **~33-40 hrs per person** |

### Critical Path

```
Day 1-2: SigNoz running ✅ → Day 3-4: Instrumentation ✅ → Day 5: Dashboard ✅ → Day 6: MCP + automation ✅ → Day 7: Submit ✅
```

**Risk:** If Day 1-2 slips, everything compresses. **Buffer:** Day 6 has 2 extra hours of overflow capacity.

---

## 5. Konsa Tools (Which Tools & Technologies)

### Core Platform

| Tool | Purpose | Why |
|---|---|---|
| **SigNoz** | Observability platform | Required by hackathon; OpenTelemetry-native |
| **Foundry** | One-click install (SigNoz + MCP) | Mandatory by rules (`casting.yaml` required) |
| **OpenTelemetry** | Instrumentation standard | Industry standard; vendor-neutral |
| **Docker** | Container runtime | Runs SigNoz + demo app locally |

### Instrumentation

| Tool | Purpose |
|---|---|
| **OpenTelemetry Python SDK** | Instrument Python Flask API |
| **OpenTelemetry Node.js SDK** | Instrument Node.js worker |
| **OpenTelemetry Collector** | Aggregate + batch telemetry before sending to SigNoz |
| **OTLP Protocol** | Export telemetry to SigNoz |

### SigNoz Features Used

| Feature | Purpose |
|---|---|
| **Query Builder** | Build SLO panels with custom metrics |
| **Dashboards** | Visualize error budget, latency, burn rate |
| **Alerts** | Warning, critical, and burn-rate alerts |
| **Logs Management** | Correlate logs with traces |
| **MCP Server** | Enable AI agent to query telemetry data |
| **API / Service Accounts** | Programmatic access for automation |

### AI / Agent

| Tool | Purpose |
|---|---|
| **LangChain** | Build the AI agent framework |
| **OpenAI / Claude API** | LLM for natural language understanding |
| **SigNoz MCP Server** | Tool that agent uses to query telemetry |
| **Flask / Streamlit** | Web UI for the agent |

### Automation

| Tool | Purpose |
|---|---|
| **n8n** | Workflow automation (webhook receiver) |
| **OR AWS Lambda** | Serverless function for webhook |
| **Docker Compose** | Scale services up/down |
| **kubectl** | (Optional) if using Kubernetes |

### Cloud & Infra

| Tool | Purpose |
|---|---|
| **AWS** | Cloud sponsor; $100 free credits for all |
| **AWS EC2** | Host SigNoz if not running locally |
| **AWS Lambda** | Auto-remediation webhook handler |
| **GitHub** | Repository + version control |

### Submission

| Tool | Purpose |
|---|---|
| **Loom / OBS** | Record demo video (2 min) |
| **YouTube** | Host demo video (unlisted) |
| **Canva / Excalidraw** | Architecture diagram |
| **Markdown** | README, blog post |

---

## 6. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User / Client Requests                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Instrumented Services (2+)                        │
│                                                                      │
│   ┌──────────────────┐          ┌──────────────────┐                │
│   │  Flask API (Py)  │          │ Node Worker (JS) │                │
│   │  - OTel SDK      │          │  - OTel SDK      │                │
│   │  - Custom spans  │◄────────►│  - Custom spans   │                │
│   │  - Logs          │          │  - Logs           │                │
│   └────────┬─────────┘          └────────┬─────────┘                │
│            │                             │                           │
│            └──────────┬──────────────────┘                           │
│                       │ OTLP Protocol                               │
│                       ▼                                              │
│           ┌─────────────────────┐                                    │
│           │  OTel Collector     │                                    │
│           │  (batch, enrich)    │                                    │
│           └──────────┬──────────┘                                    │
└──────────────────────┼───────────────────────────────────────────────┘
                       │ OTLP
                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          SigNoz (via Foundry)                        │
│                                                                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│   │  Traces  │  │ Metrics  │  │  Logs    │  │  MCP Server      │   │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
│        │              │              │                  │            │
│        ▼              ▼              ▼                  ▼            │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                  SigNoz Query Builder                        │  │
│   │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │  │
│   │  │ SLO Panels  │  │ Error Budget │  │ Burn Rate Charts   │  │  │
│   │  └─────────────┘  └──────────────┘  └────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                      Alerts                                  │  │
│   │  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐   │  │
│   │  │ Warning    │  │ Critical   │  │ Burn Rate → Webhook  │   │  │
│   │  │ (<50% SLO) │  │ (<20% SLO) │  │ (>2x for 10min)     │   │  │
│   │  └────────────┘  └────────────┘  └──────────┬───────────┘   │  │
│   └──────────────────────────────────────────────┼────────────────┘  │
└──────────────────────────────────────────────────┼───────────────────┘
                       │                            │
                       ▼                            ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│    AI Agent (LangChain)      │    │   Auto-Remediation Webhook   │
│                              │    │                              │
│  User: "Error budget?"       │    │  Alert → Lambda/n8n →        │
│  Agent queries MCP → reply  │    │  docker-compose scale /      │
│  Web UI (Flask/Streamlit)    │    │  kubectl rollout undo        │
└──────────────────────────────┘    └──────────────────────────────┘
```

---

## 7. Score Enhancement Breakdown (Judging Criteria)

### Baseline Score (Basic SLO Dashboard Only)

| Criterion | Raw | Rationale |
|---|---|---|
| Potential Impact | 7/10 | SLOs solve real problems but are well-established |
| Creativity & Innovation | 4/10 | Biggest weakness — SLO dashboards are standard practice |
| Technical Excellence | 9/10 | Can be executed cleanly with proper OTel |
| Best Use of SigNoz | 7/10 | Uses Query Builder + Dashboards + Alerts |
| User Experience | 8/10 | Intuitive dashboard organization |
| Presentation | 8/10 | Easy to explain and demonstrate |
| **Total** | **43/60 (72%)** | |

### Enhanced Score (With MCP + Automation + Polish)

| Criterion | Raw | Delta | What Changed |
|---|---|---|---|
| Potential Impact | 9/10 | **+2** | Auto-remediation makes it a closed-loop system |
| Creativity & Innovation | 8/10 | **+4** | MCP + AI agent is novel; few teams will do this |
| Technical Excellence | 10/10 | **+1** | Multi-service, cross-signal, clean code |
| Best Use of SigNoz | 10/10 | **+3** | MCP + API + Query Builder + Alerts + Logs — full stack |
| User Experience | 8/10 | 0 | Already solid |
| Presentation | 10/10 | **+2** | Scripted demo, polished README, architecture diagram |
| **Total** | **55/60 (92%)** | **+12** | |

### Enhancement ROI Ranking

| Enhancement | Criteria Boosted | Effort | ROI |
|---|---|---|---|
| MCP + LangChain agent | Creativity (+4), SigNoz depth (+3) | Medium (4-6 hrs) | **Highest** |
| Auto-remediation webhook | Impact (+2) | Medium (4 hrs) | High |
| Polished README + demo | Presentation (+2) | Low (2 hrs) | High |
| Multi-service instrumentation | SigNoz depth (+1), Technical (+1) | Low (2 hrs) | Medium |
| Logs/traces/metrics correlation | SigNoz depth (+1), Technical (+1) | Medium (3 hrs) | Medium |
| Blog post | Side track prize (LEGO) | Low (1 hr) | Bonus |

---

## 8. Win Probability Estimate

### Scenario Analysis

| Scenario | Track 2 1st Place | Track 2 Top 3 | AWS Credits (Overall Top 3) |
|---|---|---|---|
| Basic SLO dashboard (no extras) | ~12-15% | ~25-30% | <5% |
| SLO + MCP agent | ~25-30% | ~45-50% | ~8-10% |
| SLO + MCP + automation + polish | **~35-40%** | **~55-65%** | **~12-15%** |
| SLO + MCP + automation + polish + blog + social | **~40-45%** | **~60-70%** | **~15-18%** |

### Factors That Affect Our Odds

| Factor | Impact on Probability |
|---|---|
| Track 2 is less competitive than Track 1 (AI) | **+15-20%** vs Track 1 |
| Most teams submit last-minute, half-baked projects | **+10-15%** for early preparation |
| MCP integration is rare — most teams won't attempt it | **+10-15%** unique advantage |
| Judges see many dashboards — cross-signal + automation stands out | **+5-10%** differentiation |
| Demo quality heavily influences non-technical judges | **+5-10%** for a scripted, clear video |

### The Real Winning Strategy

> **A perfect SLO pack = 15% chance.**
> **A perfect SLO pack + MCP + automation + killer demo = 40% chance.**
> **The remaining 60% depends on:**
> - How many teams register (more = harder)
> - Whether a truly exceptional project appears (can't control)
> - Judge mood and preferences (can't control)

**Conclusion:** Focus on what you can control (MCP, automation, demo) and accept the uncertainty. Even at 40%, that is **~2.5x higher than most teams' odds.**

---

## 9. Risk Assessment & Mitigation

### Risk Matrix

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Foundry / Docker issues on Windows | Medium | High | Start Day 1; have WSL2 backup; test Docker Desktop compatibility |
| SigNoz MCP integration is complex | Medium | Medium | Read SigNoz MCP docs in advance (Resources page has 6 blog posts) |
| Team member drops out | Low | High | Both learn all parts; no single point of failure |
| AWS credit not arriving | Low | High | Self-host locally if credits delayed; AWS is optional for core project |
| Demo video too long | Medium | Medium | Write script first, time each segment, keep under 2:00 |
| OTel instrumentation bugs | Medium | Medium | Use the demo app as a reference; copy patterns from SigNoz docs |
| Running out of time for MCP | Medium | High | Cut auto-remediation first (lowest incremental ROI); keep MCP (highest ROI) |
| Judge does not understand SLOs | Low | Medium | Explain in README + demo clearly; assume basic SRE knowledge |
| Another team builds the same thing | Low | High | Execute faster; add one unique feature (we chose MCP agent) |

### Fallback Plan (If Time Runs Short)

| Priority | Must Have | Nice to Have | Can Drop |
|---|---|---|---|
| 1 | SigNoz running + telemetry | MCP agent | Auto-remediation |
| 2 | SLO dashboard + alerts | Auto-remediation | Blog post |
| 3 | Demo video + README | Blog post | Social media posts |
| 4 | MCP agent | Social media posts | — |

**Golden Rule:** Never sacrifice the demo video. A project with a perfect dashboard but no demo scores lower than a decent dashboard with a clear, compelling demo.

---

## Appendix: Quick Reference

### Useful Links

| Resource | URL |
|---|---|
| SigNoz Docs | https://signoz.io/docs |
| Foundry Quickstart | https://signoz.io/docs/install/docker/ |
| SigNoz MCP Server | https://signoz.io/docs/ai/signoz-mcp-server/ |
| Query Builder Guide | https://signoz.io/docs/userguide/query-builder-v5/ |
| Alerts Guide | https://signoz.io/docs/alerts/ |
| OTel Python SDK | https://opentelemetry.io/docs/languages/python/ |
| OTel Node.js SDK | https://opentelemetry.io/docs/languages/js/ |
| SigNoz Slack | https://signoz-community.slack.com/ |
| Hackathon Rules | https://www.wemakedevs.org/hackathons/signoz/rules |
| Project Ideas | https://github.com/orgs/SigNoz/projects/65 |

### Command Cheat Sheet

```bash
# Install Foundry + SigNoz
curl -sL https://github.com/SigNoz/foundry/releases/latest/download/install.sh | bash
foundry deploy

# Deploy OTel demo app
git clone https://github.com/SigNoz/opentelemetry-demo-lite
cd opentelemetry-demo-lite && docker-compose up

# Verify SigNoz is running
docker ps | grep signoz

# Export dashboard (from SigNoz UI)
# Settings → Dashboard → Export JSON

# Commit casting files (required by rules)
git add casting.yaml casting.yaml.lock
git commit -m "Initial SigNoz deployment config"
```

---

*Report prepared for Agents of SigNoz Hackathon — Track 2: Signals & Dashboards*
*Team: Rudra & Het Patel — KPGU*
