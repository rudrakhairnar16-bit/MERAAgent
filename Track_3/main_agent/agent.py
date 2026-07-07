import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI as OpenAIBase
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

load_dotenv()

resource = Resource(attributes={
    "service.name": "mera-main-agent",
    "service.version": "1.0.0",
    "deployment.environment": "production"
})
provider = TracerProvider(resource=resource)
endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", timeout=1)
provider.add_span_processor(BatchSpanProcessor(exporter, schedule_delay_millis=5000, max_queue_size=1024))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)


class PRReviewAgent:
    def __init__(self, model: str = ""):
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.client = OpenAIBase(base_url=ollama_url, api_key="ollama")
        self.review_history: list[dict] = []

    def review_code(self, code_snippet: str, language: str = "python") -> dict:
        with tracer.start_as_current_span("pr_review") as span:
            span.set_attribute("code.language", language)
            span.set_attribute("code.length", len(code_snippet))
            span.set_attribute("agent.task", "code_review")

            start = time.time()
            review = self._call_llm_for_review(code_snippet, language)
            latency_ms = (time.time() - start) * 1000

            span.set_attribute("llm.latency_ms", latency_ms)
            span.set_attribute("llm.model", self.model)
            span.set_attribute("review.issues_count", len(review.get("issues", [])))
            span.set_attribute("review.confidence_score", review.get("confidence", 0))

            self.review_history.append({
                "timestamp": time.time(),
                "language": language,
                "issues": review.get("issues", []),
                "confidence": review.get("confidence", 0),
                "latency_ms": latency_ms
            })

            span.add_event("review_completed", {
                "issues_found": len(review.get("issues", [])),
                "latency_ms": latency_ms
            })
            return review

    def _call_llm_for_review(self, code: str, language: str) -> dict:
        with tracer.start_as_current_span("llm_call") as span:
            span.set_attribute("llm.call_type", "review_generation")
            span.set_attribute("llm.input_length", len(code))

            prompt = (
                f"Review this {language} code. Return ONLY valid JSON with no explanation:\n"
                '{"issues": [{"line": 1, "severity": "warning", "message": "desc", "suggestion": "fix"}], '
                '"confidence": 0.95, "summary": "overall"}\n\n'
                f"Code:\n```{language}\n{code}\n```"
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a code reviewer. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2048
                )
                content = response.choices[0].message.content.strip()
                span.set_attribute("llm.response_length", len(content))
            except Exception as e:
                span.record_exception(e)
                return {"issues": [], "confidence": 0.0, "summary": f"LLM call failed: {str(e)}"}

            result = self._try_parse_json(content)
            if result is None:
                span.set_attribute("llm.parse_error", True)
                return {"issues": [], "confidence": 0.0, "summary": "Failed to parse LLM response"}

            conf = result.get("confidence", 0)
            if isinstance(conf, (int, float)) and conf < 0.5:
                span.set_attribute("llm.low_confidence", True)
                span.add_event("low_confidence_warning", {"confidence": conf})

            return result

    def _try_parse_json(self, text: str) -> dict | None:
        import re
        for attempt in [text.strip(), text.strip().strip("`"), text.strip().strip("`").strip("json")]:
            if attempt.startswith("{"):
                try:
                    return json.loads(attempt)
                except json.JSONDecodeError:
                    pass
        m = re.search(r'\{.*"issues".*"summary".*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
        return None

    def get_anomaly_score(self) -> float:
        recent = self.review_history[-10:] if len(self.review_history) > 10 else self.review_history
        if not recent:
            return 0.0
        avg_confidence = sum(r["confidence"] for r in recent) / len(recent)
        if avg_confidence < 0.5:
            return 0.8
        avg_issues = sum(len(r["issues"]) for r in recent) / len(recent)
        if avg_issues > 5:
            return 0.6
        return 0.1


if __name__ == "__main__":
    agent = PRReviewAgent()
    code = 'def add(a,b): return a+b\nprint(add(1,2))'
    print(json.dumps(agent.review_code(code), indent=2))
    print(f"Anomaly score: {agent.get_anomaly_score()}")
