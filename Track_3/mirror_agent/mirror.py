import os
import sys
import json
import time
import requests
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI as OpenAIBase
from opentelemetry import trace

load_dotenv()
from signoz_config.tracing import get_tracer, force_flush, get_current_trace_id
from state import get_state, save_state
from mirror_agent.detector import AdaptiveDetector, AnomalyResult
from mirror_agent.healer import ActionExecutor

tracer = get_tracer("mera-mirror-agent")


class MirrorAgent:
    MCP_URLS = [
        "http://localhost:8000/mcp",
        "http://localhost:8080/mcp",
        "http://signoz-mcp:8000/mcp",
    ]
    AUTH_HEADERS = ["SIGNOZ-API-KEY", "Authorization", "X-SigNoz-API-Key"]

    def __init__(self):
        env_url = os.getenv("SIGNOZ_MCP_URL", "").strip()
        self.mcp_urls = [env_url] if env_url else list(self.MCP_URLS)
        self.api_key = os.getenv("SIGNOZ_API_KEY", "")
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.client = OpenAIBase(base_url=ollama_url, api_key="ollama")
        self.detector = AdaptiveDetector()
        self.healer = ActionExecutor(agent_instance=self)
        self.detected_anomalies: list[dict] = []
        self.applied_fixes: list[dict] = []
        self.latency_before: float = 0.0
        self.confidence_before: float = 0.0
        self._mcp_healthy: bool = False

    def _mcp_call(self, method: str, params: dict, req_id: int = 1) -> dict:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}
        for url in self.mcp_urls:
            for auth_header in self.AUTH_HEADERS:
                for attempt in range(2):
                    headers = {"Content-Type": "application/json"}
                    if self.api_key:
                        headers[auth_header] = self.api_key
                    try:
                        resp = requests.post(url, json=payload, headers=headers, timeout=5)
                        if resp.status_code == 200:
                            self._mcp_healthy = True
                            return resp.json().get("result", {})
                        if resp.status_code == 401 and attempt == 0:
                            continue
                    except requests.ConnectionError:
                        continue
                    except Exception:
                        continue
        self._mcp_healthy = False
        return {"error": f"MCP call failed: {method}"}

    def check_mcp_health(self) -> dict:
        result = {"reachable": False, "authenticated": False, "url": "", "tools_count": 0}
        for url in self.mcp_urls:
            for auth_header in self.AUTH_HEADERS:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers[auth_header] = self.api_key
                try:
                    resp = requests.post(
                        url,
                        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1},
                        headers=headers,
                        timeout=5
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        tools = data.get("result", {}).get("tools", [])
                        result["reachable"] = True
                        result["authenticated"] = True
                        result["url"] = url
                        result["tools_count"] = len(tools)
                        self._mcp_healthy = True
                        return result
                    elif resp.status_code == 401:
                        result["reachable"] = True
                        result["url"] = url
                except requests.ConnectionError:
                    continue
                except Exception:
                    continue
        self._mcp_healthy = False
        return result

    def _get_simulated_traces(self, service: str = "mera-main-agent", limit: int = 10) -> list:
        traces = []
        import random
        for i in range(limit):
            trace_id = f"sim-{i}-{random.randint(10000,99999)}"
            span_count = random.randint(1, 4)
            spans = []
            for j in range(span_count):
                lat = random.choice([200, 500, 3000, 7000, 15000, 100])
                spans.append({
                    "span_id": f"s{i}-{j}",
                    "name": random.choice(["pr_review", "llm_call", "code_analysis", "format_check"]),
                    "duration_ms": lat,
                    "attributes": {
                        "code.language": random.choice(["python", "javascript", "go"]),
                        "code.length": str(random.randint(100, 2000)),
                        "review.issues_count": str(random.randint(0, 5)),
                        "llm.low_confidence": "true" if random.random() < 0.3 else "false",
                        "llm.latency_ms": str(lat)
                    }
                })
            traces.append({"trace_id": trace_id, "spans": spans, "service_name": service})
        return traces

    def query_recent_traces(self, service: str = "mera-main-agent", limit: int = 10) -> list:
        with tracer.start_as_current_span("mirror.query_traces") as span:
            span.set_attribute("mirror.query_type", "recent_traces")
            span.set_attribute("mirror.service_target", service)
            current_trace_id = get_current_trace_id()
            if current_trace_id:
                span.set_attribute("root_trace_id", current_trace_id)
            result = self._mcp_call("traces/list", {
                "service": service, "limit": limit, "order": "desc"
            })
            traces = result if isinstance(result, list) else []
            span.set_attribute("mirror.traces_fetched", len(traces))
            span.add_event("traces_fetched", {"count": len(traces)})
            return traces

    def query_alerts(self, status: str = "firing") -> list:
        with tracer.start_as_current_span("mirror.query_alerts") as span:
            current_trace_id = get_current_trace_id()
            if current_trace_id:
                span.set_attribute("root_trace_id", current_trace_id)
            result = self._mcp_call("alerts/list", {"status": status})
            alerts = result if isinstance(result, list) else []
            span.set_attribute("mirror.alerts_fetched", len(alerts))
            return alerts

    def analyze_trace_anomalies(self, traces: list) -> list:
        with tracer.start_as_current_span("mirror.analyze_anomalies") as span:
            current_trace_id = get_current_trace_id()
            if current_trace_id:
                span.set_attribute("root_trace_id", current_trace_id)
            anomalies = []
            for t in traces:
                for s in t.get("spans", []):
                    lat = s.get("duration_ms", 0)
                    result = self.detector.check_latency(
                        duration_ms=lat,
                        span_name=s.get("name", ""),
                        span_id=s.get("span_id", ""),
                        trace_id=t.get("trace_id", "")
                    )
                    if result is not None:
                        anomalies.append({
                            "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                            "type": "high_latency", "severity": result.severity,
                            "value_ms": lat,
                            "threshold_ms": round(result.mean + 2 * result.std, 0),
                            "z_score": result.z_score,
                            "message": result.message,
                            "resolved": False
                        })
                    attrs = s.get("attributes", {})
                    conf_str = attrs.get("review.confidence", "")
                    if conf_str:
                        try:
                            conf_val = float(conf_str)
                            result = self.detector.check_confidence(
                                confidence=conf_val,
                                span_id=s.get("span_id", ""),
                                trace_id=t.get("trace_id", "")
                            )
                            if result is not None:
                                anomalies.append({
                                    "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                                    "type": "low_confidence", "severity": result.severity,
                                    "confidence": conf_val, "z_score": result.z_score,
                                    "message": result.message,
                                    "resolved": False
                                })
                        except (ValueError, TypeError):
                            pass
                    if attrs.get("llm.low_confidence") == "true" and not conf_str:
                        result = self.detector.check_confidence(
                            confidence=0.3,
                            span_id=s.get("span_id", ""),
                            trace_id=t.get("trace_id", "")
                        )
                        if result is not None:
                            anomalies.append({
                                "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                                "type": "low_confidence", "severity": result.severity,
                                "confidence": 0.3, "z_score": result.z_score,
                                "message": result.message,
                                "resolved": False
                            })
                    ic = attrs.get("review.issues_count", "0")
                    cl = attrs.get("code.length", "0")
                    if ic == "0" and cl.isdigit() and int(cl) > 100:
                        result = self.detector.check_issues(
                            issues_count=0,
                            code_length=int(cl),
                            span_id=s.get("span_id", ""),
                            trace_id=t.get("trace_id", "")
                        )
                        if result is not None:
                            anomalies.append({
                                "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                                "type": "zero_issues_suspicious", "severity": result.severity,
                                "code_length": int(cl), "z_score": result.z_score,
                                "message": result.message,
                                "resolved": False
                            })
            span.set_attribute("mirror.anomalies_detected", len(anomalies))
            for a in anomalies:
                span.add_event("anomaly_detected", a)
            self.detected_anomalies.extend(anomalies)
            return anomalies

    def _try_parse_json(self, text: str) -> dict | None:
        import re
        text = text.strip()
        for prefix in ["", "`", "`json"]:
            cleaned = text.strip(prefix).strip()
            if cleaned.startswith("{"):
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    pass
        m = re.search(r'\{.*"fix".*"action".*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        return None

    def generate_fix_suggestion(self, anomaly: dict) -> dict:
        with tracer.start_as_current_span("mirror.generate_fix") as span:
            current_trace_id = get_current_trace_id()
            if current_trace_id:
                span.set_attribute("root_trace_id", current_trace_id)
            span.set_attribute("mirror.anomaly_type", anomaly.get("type", ""))
            span.set_attribute("mirror.anomaly_severity", anomaly.get("severity", ""))
            fix_action = self.healer.apply_fix(anomaly)
            prompt = (
                f"Anomaly: {anomaly.get('message')} | "
                f"Type: {anomaly.get('type')} | Severity: {anomaly.get('severity')}. "
                "Describe this auto-fix action in human language. "
                "Return ONLY valid JSON: "
                '{"fix": "<description>", "action": "<action_type>", "priority": "high|medium|low"}'
            )
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024
                )
                result = self._try_parse_json(response.choices[0].message.content)
                if result is None:
                    result = {
                        "fix": f"Auto-fix executed: {fix_action.get('action', 'unknown')}",
                        "action": fix_action.get("action", "alert"),
                        "priority": fix_action.get("improvement", 0.5) > 0.3 and "high" or "medium"
                    }
                else:
                    result["fix"] = f"{result.get('fix', '')} [auto: {fix_action.get('action', 'unknown')}]"
                    result["action"] = fix_action.get("action", result.get("action", "alert"))
            except Exception as e:
                result = {
                    "fix": f"Auto-fix: {fix_action.get('action', 'unknown')} (LLM desc failed: {e})",
                    "action": fix_action.get("action", "alert"),
                    "priority": "medium"
                }
            result["executed"] = fix_action.get("executed", False)
            result["success"] = fix_action.get("success", False)
            result["improvement"] = fix_action.get("improvement", 0.0)
            span.set_attribute("mirror.fix_action", result.get("action", "unknown"))
            span.set_attribute("mirror.fix_priority", result.get("priority", "low"))
            span.set_attribute("mirror.fix_executed", result.get("executed", False))
            span.set_attribute("mirror.fix_success", result.get("success", False))
            self.applied_fixes.append(result)
            return result

    def get_before_after_metrics(self) -> dict:
        baseline = self.detector.get_baseline_summary()
        latency_info = baseline.get("latency_ms", {})
        confidence_info = baseline.get("confidence", {})
        actions = self.healer.get_summary()
        return {
            "latency": {
                "before": self.latency_before if self.latency_before else latency_info.get("mean", 0),
                "after": latency_info.get("mean", 0),
                "improvement_pct": round(
                    (self.latency_before - latency_info.get("mean", 0)) / max(self.latency_before, 1) * 100, 1
                ) if self.latency_before and latency_info.get("mean") else 0.0
            },
            "confidence": {
                "baseline": confidence_info.get("mean", 0),
                "samples": confidence_info.get("count", 0)
            },
            "actions": actions,
            "sample_count": latency_info.get("count", 0)
        }

    def get_baseline_state(self) -> dict:
        return self.detector.get_baseline_summary()

    def create_signoz_dashboard(self) -> bool:
        with tracer.start_as_current_span("mirror.create_dashboard") as span:
            ok = self._mcp_call("dashboards/create", {
                "title": "MERA - Mirror Entity Recursive Agent",
                "panels": [
                    {"title": "Review Latency", "query": "avg(duration_ms) WHERE service.name='mera-main-agent'", "type": "timeseries"},
                    {"title": "LLM Confidence", "query": "avg(attributes.review.confidence_score) WHERE service.name='mera-main-agent'", "type": "gauge"},
                    {"title": "Anomalies", "query": "count(attributes.mirror.anomalies_detected) WHERE service.name='mera-mirror-agent'", "type": "timeseries"},
                    {"title": "Auto-Fixes", "query": "count(attributes.mirror.fix_action) WHERE service.name='mera-mirror-agent'", "type": "stat"}
                ]
            })
            span.set_attribute("mirror.dashboard_created", bool(ok))
            return bool(ok)

    def create_alert_rules(self) -> bool:
        with tracer.start_as_current_span("mirror.create_alerts") as span:
            rules = [
                {"name": "MERA-High-Latency", "condition": "avg(duration_ms) > 5000", "severity": "warning"},
                {"name": "MERA-Low-Confidence", "condition": "avg(attributes.review.confidence_score) < 0.5", "severity": "critical"},
                {"name": "MERA-Anomaly-Spike", "condition": "count(attributes.mirror.anomalies_detected) > 10", "severity": "warning"}
            ]
            for r in rules:
                self._mcp_call("alerts/create", r)
            span.set_attribute("mirror.alerts_created", len(rules))
            return True


def probe_mcp() -> dict:
    probe = MirrorAgent()
    return probe.check_mcp_health()


def run_self_healing_cycle() -> list:
    mirror = MirrorAgent()
    state = get_state()
    saved_baseline = state.get("detector_baseline", {})
    if saved_baseline:
        mirror.detector.load_state(saved_baseline)
        total = mirror.detector.total_samples()
        if total:
            print(f"  Loaded baseline from {total} historical samples")
    fast = os.environ.get("DEMO_FAST") == "1" or "--fast" in sys.argv
    print("\n[Mirror Agent] Self-healing cycle starting...")
    with tracer.start_as_current_span("self_healing_cycle") as span:
        current_trace_id = get_current_trace_id()
        if current_trace_id:
            span.set_attribute("root_trace_id", current_trace_id)
        use_simulated = False
        if fast:
            print("  FAST mode — using simulated traces (skipping MCP)")
            traces = mirror._get_simulated_traces(limit=12)
            alerts = []
            use_simulated = True
        else:
            mcp_health = mirror.check_mcp_health()
            span.set_attribute("mcp.reachable", mcp_health["reachable"])
            span.set_attribute("mcp.authenticated", mcp_health["authenticated"])
            if mcp_health["reachable"] and mcp_health["authenticated"]:
                print(f"  MCP connected [{mcp_health['url']}] — {mcp_health['tools_count']} tools")
                traces = mirror.query_recent_traces(limit=15)
                alerts = mirror.query_alerts()
            else:
                reason = "unreachable" if not mcp_health["reachable"] else "unauthenticated"
                print(f"  MCP {reason} — using simulated traces")
                traces = mirror._get_simulated_traces(limit=12)
                alerts = []
                use_simulated = True
                if not mcp_health["reachable"]:
                    print("  Tip: Start SigNoz with: docker compose up -d  or  foundryctl cast -f casting.yaml")
                if not mcp_health["authenticated"]:
                    print("  Tip: Set SIGNOZ_API_KEY in .env (generate via: python scripts/setup_api_key.py)")
        anomalies = mirror.analyze_trace_anomalies(traces)
        print(f"  Traces: {len(traces)} | Alerts: {len(alerts)} | Anomalies: {len(anomalies)}")
        if anomalies:
            for a in anomalies:
                fix = mirror.generate_fix_suggestion(a)
                print(f"  Fix [{a['type']}] ({fix.get('action', 'N/A')}): {fix.get('fix', 'N/A')[:70]}...")
            if mcp_health["reachable"] and mcp_health["authenticated"]:
                mirror.create_signoz_dashboard()
                mirror.create_alert_rules()
                print("  Dashboard + alerts created/updated")
        else:
            print("  System healthy — no anomalies detected")
        baseline = mirror.get_before_after_metrics()
        span.set_attribute("cycle.anomalies", len(anomalies))
        span.set_attribute("cycle.alerts_present", len(alerts))
        span.set_attribute("mirror.simulated_mode", use_simulated)
        span.set_attribute("cycle.fix_actions", mirror.healer.get_summary().get("total_actions", 0))
        span.set_attribute("cycle.fix_success_rate", mirror.healer.get_summary().get("successful", 0) / max(mirror.healer.get_summary().get("total_actions", 1), 1))
        if baseline.get("latency", {}).get("improvement_pct"):
            span.set_attribute("cycle.latency_improvement_pct", baseline["latency"]["improvement_pct"])
    detector_state = mirror.detector.save_state()
    state = get_state()
    state["detector_baseline"] = detector_state
    total_samples = mirror.detector.total_samples()
    if "baseline" not in state or not isinstance(state.get("baseline"), dict):
        state["baseline"] = {}
    state["baseline"]["total_samples"] = total_samples
    save_state(state)
    span.set_attribute("cycle.baseline_samples", total_samples)
    force_flush()
    print(f"  Baseline saved ({total_samples} total samples)")
    print("[Mirror Agent] Cycle complete.\n")
    return anomalies


if __name__ == "__main__":
    run_self_healing_cycle()
