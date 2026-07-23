import json
import os
import threading
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any

_lock = threading.Lock()

DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "mera_state.json"


@dataclass
class BaselineMetrics:
    mean_latency: float = 0.0
    std_latency: float = 0.0
    mean_confidence: float = 0.0
    std_confidence: float = 0.0
    mean_issues: float = 0.0
    std_issues: float = 0.0
    sample_count: int = 0
    improvement_pct_latency: float = 0.0
    improvement_pct_confidence: float = 0.0


@dataclass
class CycleData:
    cycle: int
    anomalies: int = 0
    fixes: int = 0
    traces: int = 0
    alerts: int = 0
    timestamp: str = ""
    error: str = ""
    latency_before: float = 0.0
    latency_after: float = 0.0
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    self_healed: bool = False


@dataclass
class ReviewData:
    cycle: int = 0
    language: str = ""
    issues_count: int = 0
    confidence: float = 0.0
    summary: str = ""
    timestamp: float = 0.0


@dataclass
class AnomalyData:
    span_id: str = ""
    trace_id: str = ""
    type: str = ""
    severity: str = "warning"
    value_ms: float = 0.0
    threshold_ms: float = 0.0
    message: str = ""
    resolved: bool = False
    fix_action: str = ""
    improvement_ms: float = 0.0


@dataclass
class FixData:
    anomaly_type: str = ""
    action: str = ""
    priority: str = "low"
    fix: str = ""
    executed: bool = False
    success: bool = False
    improvement: float = 0.0


@dataclass
class AppState:
    cycles: list = field(default_factory=list)
    reviews: list = field(default_factory=list)
    anomalies: list = field(default_factory=list)
    fixes: list = field(default_factory=list)
    alerts: list = field(default_factory=list)
    dashboard_url: str = "http://localhost:8080"
    status: str = "idle"
    baseline: dict = field(default_factory=lambda: asdict(BaselineMetrics()))
    detector_baseline: dict = field(default_factory=dict)


def _default_state() -> dict:
    return asdict(AppState())


def get_state() -> dict:
    with _lock:
        if not STATE_FILE.exists():
            return _default_state()
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return _default_state()


def save_state(state: dict) -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def append_cycle(cycle_data: dict) -> None:
    state = get_state()
    state["cycles"].append({**cycle_data, "timestamp": str(cycle_data.get("timestamp", ""))})
    state["status"] = f"Cycle {len(state['cycles'])} complete"
    save_state(state)


def append_review(review_data: dict) -> None:
    state = get_state()
    state["reviews"].append(review_data)
    save_state(state)


def append_anomalies(anomalies: list) -> None:
    state = get_state()
    state["anomalies"].extend(anomalies)
    save_state(state)


def append_fixes(fixes: list) -> None:
    state = get_state()
    state["fixes"].extend(fixes)
    save_state(state)


def update_alerts(alert_count: int) -> None:
    state = get_state()
    state["alerts"] = alert_count
    save_state(state)


def update_baseline(baseline: dict) -> None:
    state = get_state()
    state["baseline"] = baseline
    save_state(state)


def reset_state() -> None:
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(_default_state(), indent=2), encoding="utf-8")
