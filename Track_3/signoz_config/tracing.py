"""Shared OpenTelemetry tracing setup — single TracerProvider for all agents."""
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

_tracer = None
_provider = None


_exporter = None


def force_flush():
    global _provider
    if _provider is not None:
        try:
            _provider.force_flush(timeout_millis=5000)
        except Exception:
            pass


def get_tracer(service_name: str = "mera") -> trace.Tracer:
    global _tracer, _provider
    if _tracer is not None:
        return _tracer

    resource = Resource(attributes={
        "service.name": service_name,
        "service.version": "1.0.0",
    })
    global _exporter
    _provider = TracerProvider(resource=resource)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    try:
        _exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", timeout=1)
        _provider.add_span_processor(BatchSpanProcessor(_exporter, schedule_delay_millis=1000, max_queue_size=1024))
    except Exception:
        pass
    trace.set_tracer_provider(_provider)
    _tracer = trace.get_tracer(__name__)
    return _tracer
