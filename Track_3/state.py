import json
import os
import threading
from pathlib import Path

_lock = threading.Lock()

DATA_DIR = Path(__file__).parent / "data"
STATE_FILE = DATA_DIR / "mera_state.json"

DEFAULT_STATE = {
    "cycles": [],
    "reviews": [],
    "anomalies": [],
    "fixes": [],
    "alerts": [],
    "dashboard_url": "http://localhost:8080",
    "status": "idle"
}


def get_state() -> dict:
    with _lock:
        if not STATE_FILE.exists():
            return dict(DEFAULT_STATE)
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_STATE)


def save_state(state: dict):
    with _lock:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def append_cycle(cycle_data: dict):
    state = get_state()
    state["cycles"].append({
        **cycle_data,
        "timestamp": str(cycle_data.get("timestamp", ""))
    })
    state["status"] = f"Cycle {len(state['cycles'])} complete"
    save_state(state)


def append_review(review_data: dict):
    state = get_state()
    state["reviews"].append(review_data)
    save_state(state)


def append_anomalies(anomalies: list):
    state = get_state()
    state["anomalies"].extend(anomalies)
    save_state(state)


def append_fixes(fixes: list):
    state = get_state()
    state["fixes"].extend(fixes)
    save_state(state)


def update_alerts(alert_count: int):
    state = get_state()
    state["alerts"] = alert_count
    save_state(state)
