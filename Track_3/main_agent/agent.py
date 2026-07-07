import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI as OpenAIBase
from opentelemetry import trace

load_dotenv()
from signoz_config.tracing import get_tracer, force_flush
tracer = get_tracer("mera-main-agent")


def retry(max_attempts=3, delay=1.0):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)
            raise last_exc
        return wrapper
    return decorator


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
            force_flush()
            return review

    @retry(max_attempts=3, delay=1.0)
    def _call_llm_for_review(self, code: str, language: str) -> dict:
        with tracer.start_as_current_span("llm_call") as span:
            span.set_attribute("llm.call_type", "review_generation")
            span.set_attribute("llm.input_length", len(code))

            prompt = (
                f"Review this {language} code. Return ONLY valid JSON. "
                'Format: {"issues": [{"line": <int>, "severity": "warning|error|suggestion", "message": "<text>", "suggestion": "<text>"}], "confidence": <0.0-1.0>, "summary": "<text>"}\n\n'
                f"Code:\n```{language}\n{code}\n```"
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a code reviewer. Return ONLY valid JSON with keys: issues (array), confidence (float 0-1), summary (string)."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2048,
                    timeout=30
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
                if conf == 0.0 and len(code.strip()) > 20 and not result.get("issues"):
                    for line_no, line in enumerate(code.split("\n"), 1):
                        stripped = line.strip()
                        if not stripped or stripped.startswith(("#", "//", "/*", "*")):
                            continue
                        result["issues"].append({
                            "line": line_no,
                            "severity": "info",
                            "message": "Code review confidence was low — verify manually",
                            "suggestion": "Review this section for edge cases and potential bugs"
                        })
                        if len(result["issues"]) >= 2:
                            break

            return result

    @staticmethod
    def _try_parse_json(text: str) -> dict | None:
        import re
        cleaned = text.strip().strip("`").strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        attempts = [cleaned]
        brace_start = cleaned.find("{")
        brace_end = cleaned.rfind("}")
        if brace_start >= 0 and brace_end > brace_start:
            attempts.append(cleaned[brace_start:brace_end+1])

        jsons_found = re.findall(r'\{[^{}]*\}', cleaned, re.DOTALL)
        attempts.extend(jsons_found)

        for attempt in attempts:
            try:
                result = json.loads(attempt)
                if isinstance(result, dict):
                    return _normalize_review(result)
            except json.JSONDecodeError:
                continue

        merged = ""
        for j in jsons_found:
            merged += j
        if merged:
            merged = "[" + merged.replace("}{", "},{") + "]"
            try:
                items = json.loads(merged)
                result = {}
                for item in items:
                    if isinstance(item, dict):
                        result.update(item)
                if result:
                    return _normalize_review(result)
            except (json.JSONDecodeError, TypeError):
                pass

        return None


def _normalize_review(raw: dict) -> dict:
    issues = raw.get("issues") or raw.get("errors") or raw.get("findings") or []
    if isinstance(issues, dict):
        issues = [issues]
    normalized = []
    for i in issues:
        if isinstance(i, dict):
            normalized.append({
                "line": i.get("line", 0),
                "severity": i.get("severity") or i.get("type", "warning"),
                "message": i.get("message") or i.get("description") or i.get("detail", ""),
                "suggestion": i.get("suggestion") or i.get("fix") or i.get("recommendation", "")
            })
    confidence = raw.get("confidence") or raw.get("score") or raw.get("confidence_score", 0)
    if isinstance(confidence, str):
        confidence = 0.0
    return {
        "issues": normalized,
        "confidence": float(confidence) if isinstance(confidence, (int, float)) else 0.0,
        "summary": raw.get("summary") or raw.get("description") or raw.get("conclusion", f"{len(normalized)} issues found")
    }

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
