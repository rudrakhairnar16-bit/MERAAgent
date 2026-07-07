import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI as OpenAIBase
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

load_dotenv()

resource = Resource(attributes={
    "service.name": "mera-mirror-agent",
    "service.version": "1.0.0",
    "mirror.role": "observer"
})
provider = TracerProvider(resource=resource)
endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", timeout=1)
provider.add_span_processor(BatchSpanProcessor(exporter, schedule_delay_millis=5000, max_queue_size=1024))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)


class MirrorAgent:
    def __init__(self):
        self.mcp_url = os.getenv("SIGNOZ_MCP_URL", "http://localhost:8080/mcp")
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.client = OpenAIBase(base_url=ollama_url, api_key="ollama")
        self.detected_anomalies: list[dict] = []

    def _mcp_call(self, method: str, params: dict, req_id: int = 1) -> dict:
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": req_id}
        try:
            resp = requests.post(self.mcp_url, json=payload, headers={
                "Content-Type": "application/json"
            }, timeout=10)
            return resp.json().get("result", {})
        except Exception as e:
            return {"error": str(e)}

    def query_recent_traces(self, service: str = "mera-main-agent", limit: int = 10) -> list:
        with tracer.start_as_current_span("mirror.query_traces") as span:
            span.set_attribute("mirror.query_type", "recent_traces")
            span.set_attribute("mirror.service_target", service)
            result = self._mcp_call("traces/list", {
                "service": service, "limit": limit, "order": "desc"
            })
            traces = result if isinstance(result, list) else []
            span.set_attribute("mirror.traces_fetched", len(traces))
            span.add_event("traces_fetched", {"count": len(traces)})
            return traces

    def query_alerts(self, status: str = "firing") -> list:
        with tracer.start_as_current_span("mirror.query_alerts") as span:
            result = self._mcp_call("alerts/list", {"status": status})
            alerts = result if isinstance(result, list) else []
            span.set_attribute("mirror.alerts_fetched", len(alerts))
            return alerts

    def analyze_trace_anomalies(self, traces: list) -> list:
        with tracer.start_as_current_span("mirror.analyze_anomalies") as span:
            anomalies = []
            for t in traces:
                for s in t.get("spans", []):
                    lat = s.get("duration_ms", 0)
                    if lat > 5000:
                        anomalies.append({
                            "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                            "type": "high_latency", "severity": "critical" if lat > 10000 else "warning",
                            "value_ms": lat, "threshold_ms": 5000,
                            "message": f"Span '{s.get('name')}' took {lat}ms"
                        })
                    attrs = s.get("attributes", {})
                    if attrs.get("llm.low_confidence") == "true":
                        anomalies.append({
                            "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                            "type": "low_confidence", "severity": "warning",
                            "message": f"Low confidence in '{s.get('name')}'"
                        })
                    ic = attrs.get("review.issues_count", "0")
                    cl = attrs.get("code.length", "0")
                    if ic == "0" and cl.isdigit() and int(cl) > 500:
                        anomalies.append({
                            "span_id": s.get("span_id"), "trace_id": t.get("trace_id"),
                            "type": "zero_issues_suspicious", "severity": "suggestion",
                            "message": f"Zero issues for {cl} chars in '{s.get('name')}'"
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
            span.set_attribute("mirror.anomaly_type", anomaly.get("type", ""))
            span.set_attribute("mirror.anomaly_severity", anomaly.get("severity", ""))
            prompt = (
                f"You are MERA Mirror. Anomaly: {anomaly.get('message')} | "
                f"Type: {anomaly.get('type')} | Severity: {anomaly.get('severity')}. "
                "Suggest a fix. Return ONLY valid JSON: "
                '{"fix": "suggestion", "action": "retry", "priority": "high"}'
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
                    return {"fix": "Could not parse LLM response", "action": "alert", "priority": "high"}
                span.set_attribute("mirror.fix_action", result.get("action", "unknown"))
                span.set_attribute("mirror.fix_priority", result.get("priority", "low"))
                return result
            except Exception as e:
                span.record_exception(e)
                return {"fix": f"Error: {str(e)}", "action": "alert", "priority": "high"}

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


def run_self_healing_cycle() -> list:
    mirror = MirrorAgent()
    print("\n[Mirror Agent] Self-healing cycle starting...")
    with tracer.start_as_current_span("self_healing_cycle") as span:
        traces = mirror.query_recent_traces(limit=15)
        alerts = mirror.query_alerts()
        anomalies = mirror.analyze_trace_anomalies(traces)
        print(f"  Traces: {len(traces)} | Alerts: {len(alerts)} | Anomalies: {len(anomalies)}")
        for a in anomalies:
            fix = mirror.generate_fix_suggestion(a)
            print(f"  Fix [{a['type']}]: {fix.get('fix', 'N/A')[:70]}...")
        if anomalies:
            mirror.create_signoz_dashboard()
            mirror.create_alert_rules()
            print("  Dashboard + alerts created/updated")
        span.set_attribute("cycle.anomalies", len(anomalies))
        span.set_attribute("cycle.alerts_present", len(alerts))
    print("[Mirror Agent] Cycle complete.\n")
    return anomalies


if __name__ == "__main__":
    run_self_healing_cycle()
