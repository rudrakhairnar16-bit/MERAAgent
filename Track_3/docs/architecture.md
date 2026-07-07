# Architecture

## Core Loop

```
Main Agent --emit--> OTel Collector --> SigNoz
                          ^
                          | MCP query
                          v
                    Mirror Agent
                          |
                    Detect anomalies?
                     /        \
                   No          Yes
                    |           |
                  Sleep      Generate fix
                    |           |
                    |       Apply / Alert
                    |           |
                    |       Update dashboard
                    |__________|
```

## Anomaly Rules

| Type | Threshold | Action |
|------|-----------|--------|
| High Latency | >5000ms | Warning |
| Critical Latency | >10000ms | Retry + Alert |
| Low Confidence | <0.5 | Investigation |
| Zero Issues | >500 chars, 0 issues | Flag |

## Integration Points

1. **OTel Traces** - Every agent operation spans
2. **Metrics** - Latency, confidence, counts
3. **Logs** - All events with trace context
4. **MCP** - Mirror queries traces/alerts programmatically
5. **Dashboard API** - Auto-create panels
6. **Alert API** - Auto-configure conditions
