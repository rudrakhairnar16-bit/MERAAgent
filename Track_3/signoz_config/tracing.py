import os
import threading
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry import context
from opentelemetry.trace import NonRecordingSpan
from opentelemetry.trace.span import SpanContext, TraceFlags

_lock = threading.RLock()
_tracer_cache: dict[str, trace.Tracer] = {}
_provider: Optional[TracerProvider] = None
_exporter_ok: bool = False


class _FallbackExporter(SpanExporter):
    def export(self, spans, timeout_millis=30000):
        return True
    def shutdown(self):
        pass
    def force_flush(self, timeout_millis=30000):
        return True


def force_flush() -> None:
    global _provider
    if _provider is not None:
        try:
            _provider.force_flush(timeout_millis=5000)
        except Exception:
            pass


def _ensure_provider() -> TracerProvider:
    global _provider, _exporter_ok
    if _provider is not None:
        return _provider
    with _lock:
        if _provider is not None:
            return _provider
        resource = Resource(attributes={
            "service.name": "mera",
            "service.version": "1.0.0",
        })
        _provider = TracerProvider(resource=resource)
        try:
            import requests
            session = requests.Session()
            session.timeout = (3, 3)
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
            exporter = OTLPSpanExporter(
                endpoint=f"{endpoint}/v1/traces",
                timeout=3,
                session=session
            )
            _provider.add_span_processor(SimpleSpanProcessor(exporter))
            _exporter_ok = True
        except Exception:
            _provider.add_span_processor(SimpleSpanProcessor(_FallbackExporter()))
        trace.set_tracer_provider(_provider)
        return _provider


def get_tracer(service_name: str = "mera") -> trace.Tracer:
    if service_name in _tracer_cache:
        return _tracer_cache[service_name]
    with _lock:
        if service_name in _tracer_cache:
            return _tracer_cache[service_name]
        provider = _ensure_provider()
        t = trace.get_tracer(f"mera.{service_name}")
        _tracer_cache[service_name] = t
        return t


def get_current_trace_id() -> Optional[str]:
    span = trace.get_current_span()
    if span is None:
        return None
    try:
        ctx = span.get_span_context()
        if ctx and ctx.trace_id != 0:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return None


def set_trace_context(trace_id_hex: str) -> None:
    if not trace_id_hex or len(trace_id_hex) != 32:
        return
    try:
        tid = int(trace_id_hex, 16)
        new_ctx = SpanContext(trace_id=tid, span_id=1, is_remote=True, trace_flags=TraceFlags(1))
        ctx = trace.set_span_in_context(NonRecordingSpan(new_ctx))
        context.attach(ctx)
    except Exception:
        pass


def trace_context_carrier() -> dict:
    tid = get_current_trace_id()
    if tid:
        return {"trace_id": tid, "service": "mera"}
    return {}
