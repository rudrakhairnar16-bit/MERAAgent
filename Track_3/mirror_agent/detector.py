import math
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MetricWindow:
    maxlen: int = 50
    values: deque = field(default_factory=lambda: deque(maxlen=50))

    def __post_init__(self):
        self.values = deque(maxlen=self.maxlen)

    def add(self, value: float) -> None:
        self.values.append(value)

    @property
    def mean(self) -> float:
        if not self.values:
            return 0.0
        return sum(self.values) / len(self.values)

    @property
    def std(self) -> float:
        if len(self.values) < 2:
            return 0.0
        m = self.mean
        variance = sum((v - m) ** 2 for v in self.values) / (len(self.values) - 1)
        return math.sqrt(variance)

    @property
    def count(self) -> int:
        return len(self.values)

    def z_score(self, value: float) -> float:
        if self.std == 0:
            return 0.0
        return (value - self.mean) / self.std


@dataclass
class AnomalyResult:
    is_anomaly: bool
    z_score: float = 0.0
    mean: float = 0.0
    std: float = 0.0
    severity: str = "warning"
    message: str = ""


class AdaptiveDetector:
    def __init__(self, z_threshold_warning: float = 2.0, z_threshold_critical: float = 3.0, min_samples: int = 3):
        self.windows: dict[str, MetricWindow] = defaultdict(MetricWindow)
        self.z_threshold_warning = z_threshold_warning
        self.z_threshold_critical = z_threshold_critical
        self.min_samples = min_samples
        self._lock = threading.Lock()
        self.anomaly_history: list[dict] = []

    def observe(self, metric_name: str, value: float) -> None:
        with self._lock:
            self.windows[metric_name].add(value)

    def check_latency(self, duration_ms: float, span_name: str = "", span_id: str = "", trace_id: str = "") -> Optional[AnomalyResult]:
        self.observe("latency_ms", duration_ms)
        window = self.windows["latency_ms"]
        if duration_ms > 10000:
            result = AnomalyResult(
                is_anomaly=True, z_score=3.0, severity="critical",
                message=f"[critical] Latency {duration_ms}ms exceeds 10s threshold"
            )
            self.anomaly_history.append({
                "type": "high_latency", "span_id": span_id, "trace_id": trace_id,
                "severity": "critical", "value_ms": duration_ms,
                "threshold_ms": 10000, "z_score": 3.0, "message": result.message
            })
            return result
        if window.count < self.min_samples:
            if duration_ms > 5000:
                result = AnomalyResult(
                    is_anomaly=True, z_score=2.0, severity="warning",
                    message=f"[warning] Latency {duration_ms}ms exceeds 5s threshold"
                )
                self.anomaly_history.append({
                    "type": "high_latency", "span_id": span_id, "trace_id": trace_id,
                    "severity": "warning", "value_ms": duration_ms,
                    "threshold_ms": 5000, "z_score": 2.0, "message": result.message
                })
                return result
            return None
        z = window.z_score(duration_ms)
        if abs(z) >= self.z_threshold_critical:
            severity = "critical"
        elif abs(z) >= self.z_threshold_warning:
            severity = "warning"
        else:
            return None
        result = AnomalyResult(
            is_anomaly=True,
            z_score=round(z, 2),
            mean=round(window.mean, 1),
            std=round(window.std, 1),
            severity=severity,
            message=f"[{severity}] Latency {duration_ms}ms z={z:.1f} (baseline: {window.mean:.0f}±{window.std:.0f}ms)"
        )
        self.anomaly_history.append({
            "type": "high_latency",
            "span_id": span_id,
            "trace_id": trace_id,
            "severity": severity,
            "value_ms": duration_ms,
            "threshold_ms": round(window.mean + self.z_threshold_warning * window.std, 0),
            "z_score": round(z, 2),
            "message": result.message
        })
        return result

    def check_confidence(self, confidence: float, span_id: str = "", trace_id: str = "") -> Optional[AnomalyResult]:
        self.observe("confidence", confidence)
        window = self.windows["confidence"]
        if window.count < self.min_samples:
            if confidence <= 0.3:
                result = AnomalyResult(
                    is_anomaly=True, severity="warning",
                    message=f"[warning] Confidence {confidence} below 0.3 threshold"
                )
                self.anomaly_history.append({
                    "type": "low_confidence", "span_id": span_id, "trace_id": trace_id,
                    "severity": "warning", "confidence": confidence,
                    "message": result.message
                })
                return result
            return None
        z = window.z_score(confidence)
        if z < -self.z_threshold_warning:
            severity = "critical" if z < -self.z_threshold_critical else "warning"
            result = AnomalyResult(
                is_anomaly=True,
                z_score=round(z, 2),
                mean=round(window.mean, 2),
                std=round(window.std, 2),
                severity=severity,
                message=f"[{severity}] Confidence {confidence} z={z:.1f} (baseline: {window.mean:.2f}±{window.std:.2f})"
            )
            self.anomaly_history.append({
                "type": "low_confidence",
                "span_id": span_id,
                "trace_id": trace_id,
                "severity": severity,
                "confidence": confidence,
                "z_score": round(z, 2),
                "message": result.message
            })
            return result
        return None

    def check_issues(self, issues_count: int, code_length: int, span_id: str = "", trace_id: str = "") -> Optional[AnomalyResult]:
        if code_length == 0:
            return None
        severity = "critical" if code_length > 1000 else "warning" if code_length > 500 else "suggestion"
        if issues_count == 0 and code_length > 100:
            result = AnomalyResult(
                is_anomaly=True, severity=severity,
                message=f"[{severity}] Zero issues for {code_length} chars — possible missed detection"
            )
            self.anomaly_history.append({
                "type": "zero_issues_suspicious",
                "span_id": span_id, "trace_id": trace_id,
                "severity": severity, "message": result.message
            })
            return result
        ratio = issues_count / code_length * 1000
        self.observe("issues_per_1k", ratio)
        window = self.windows["issues_per_1k"]
        if window.count < self.min_samples:
            return None
        z = window.z_score(ratio)
        if z < -self.z_threshold_warning and issues_count == 0 and code_length > 500:
            severity = "critical" if z < -self.z_threshold_critical else "warning"
            result = AnomalyResult(
                is_anomaly=True,
                z_score=round(z, 2),
                mean=round(window.mean, 4),
                std=round(window.std, 4),
                severity=severity,
                message=f"[{severity}] Zero issues for {code_length} chars z={z:.1f} (baseline ratio: {window.mean:.4f}/1k)"
            )
            self.anomaly_history.append({
                "type": "zero_issues_suspicious",
                "span_id": span_id,
                "trace_id": trace_id,
                "severity": severity,
                "z_score": round(z, 2),
                "message": result.message
            })
            return result
        return None

    def is_service_down(self, expected_services: set, online_services: set) -> Optional[AnomalyResult]:
        missing = expected_services - online_services
        if missing:
            msg = f"Services not reporting: {missing}"
            self.anomaly_history.append({
                "type": "service_down",
                "severity": "critical",
                "message": msg
            })
            return AnomalyResult(is_anomaly=True, severity="critical", message=msg)
        return None

    def get_baseline_summary(self) -> dict:
        result = {}
        for name, window in self.windows.items():
            result[name] = {
                "mean": round(window.mean, 2),
                "std": round(window.std, 2),
                "count": window.count
            }
        return result

    def save_state(self) -> dict:
        data = {}
        for name, window in self.windows.items():
            data[name] = list(window.values)
        data["_thresholds"] = {
            "z_warning": self.z_threshold_warning,
            "z_critical": self.z_threshold_critical,
            "min_samples": self.min_samples
        }
        return data

    def load_state(self, data: dict) -> None:
        if not data:
            return
        with self._lock:
            thresholds = data.pop("_thresholds", {})
            for name, values in data.items():
                if isinstance(values, list) and values:
                    window = self.windows[name]
                    for v in values[-window.maxlen:]:
                        window.add(v)

    def total_samples(self) -> int:
        return sum(w.count for w in self.windows.values())

    def clear_history(self) -> None:
        self.anomaly_history.clear()
