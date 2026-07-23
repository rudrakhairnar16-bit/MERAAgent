import pytest
import time
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import MirrorAgent
from mirror_agent.detector import AdaptiveDetector, MetricWindow
from mirror_agent.healer import ActionExecutor


@pytest.mark.llm
def test_main_agent_output_format():
    agent = PRReviewAgent()
    r = agent.review_code("x=1", "python")
    assert "issues" in r and "confidence" in r and "summary" in r


@pytest.mark.llm
def test_main_agent_confidence_is_float():
    agent = PRReviewAgent()
    r = agent.review_code("x=1", "python")
    assert isinstance(r.get("confidence"), (int, float))


def test_mirror_empty_traces():
    m = MirrorAgent()
    assert m.analyze_trace_anomalies([]) == []


def test_mirror_detects_high_latency():
    m = MirrorAgent()
    traces = [{"trace_id": "t1", "spans": [{"span_id": "s1", "name": "llm", "duration_ms": 6000, "attributes": {}}]}]
    assert any(a["type"] == "high_latency" for a in m.analyze_trace_anomalies(traces))


def test_mirror_detects_zero_issues():
    m = MirrorAgent()
    traces = [{"trace_id": "t2", "spans": [{"span_id": "s2", "name": "review", "duration_ms": 100, "attributes": {"review.issues_count": "0", "code.length": "1000"}}]}]
    assert any(a["type"] == "zero_issues_suspicious" for a in m.analyze_trace_anomalies(traces))


def test_mirror_multiple_anomalies():
    m = MirrorAgent()
    traces = [
        {"trace_id": "t1", "spans": [{"span_id": "s1", "name": "slow", "duration_ms": 15000, "attributes": {}}]},
        {"trace_id": "t2", "spans": [{"span_id": "s2", "name": "bad", "duration_ms": 100, "attributes": {"llm.low_confidence": "true"}}]},
        {"trace_id": "t3", "spans": [{"span_id": "s3", "name": "sus", "duration_ms": 50, "attributes": {"review.issues_count": "0", "code.length": "800"}}]}
    ]
    result = m.analyze_trace_anomalies(traces)
    types = [a["type"] for a in result]
    assert "high_latency" in types
    assert "low_confidence" in types
    assert "zero_issues_suspicious" in types


def test_mirror_no_false_positives():
    m = MirrorAgent()
    traces = [{"trace_id": "t1", "spans": [{"span_id": "s1", "name": "normal", "duration_ms": 100, "attributes": {"llm.low_confidence": "false", "review.issues_count": "3", "code.length": "200"}}]}]
    assert len(m.analyze_trace_anomalies(traces)) == 0


def test_anomaly_high_latency_critical_threshold():
    m = MirrorAgent()
    traces = [{"trace_id": "t1", "spans": [{"span_id": "s1", "name": "very_slow", "duration_ms": 12000, "attributes": {}}]}]
    anomalies = m.analyze_trace_anomalies(traces)
    assert any(a["severity"] == "critical" for a in anomalies)


def test_state_module():
    from state import get_state, append_cycle, save_state
    save_state({"cycles": [], "reviews": [], "anomalies": [], "fixes": [], "alerts": [], "dashboard_url": "", "status": "test", "baseline": {}, "detector_baseline": {}})
    append_cycle({"cycle": 1, "anomalies": 1, "fixes": 1, "traces": 1, "alerts": 1, "timestamp": time.time()})
    s = get_state()
    assert len(s["cycles"]) == 1
    assert s["cycles"][0]["cycle"] == 1


# ====== Adaptive Detector Tests ======

def test_metric_window_init():
    w = MetricWindow(maxlen=10)
    assert w.mean == 0.0
    assert w.std == 0.0
    assert w.count == 0


def test_metric_window_basic_stats():
    w = MetricWindow(maxlen=100)
    for v in [10, 20, 30, 40, 50]:
        w.add(v)
    assert w.mean == 30.0
    assert w.count == 5
    assert w.std > 0


def test_metric_window_maxlen():
    w = MetricWindow(maxlen=3)
    for v in range(10):
        w.add(v)
    assert w.count == 3
    assert list(w.values) == [7, 8, 9]


def test_metric_window_z_score():
    w = MetricWindow(maxlen=100)
    for v in range(1, 101):
        w.add(v)
    z = w.z_score(100)
    assert abs(z - 1.65) < 0.3


def test_adaptive_detector_requires_min_samples():
    d = AdaptiveDetector(min_samples=5)
    result = d.check_latency(2000)
    assert result is None


def test_adaptive_detector_detects_after_min_samples():
    d = AdaptiveDetector(min_samples=3, z_threshold_warning=1.0)
    for v in [100, 110, 90]:
        d.observe("latency_ms", v)
    result = d.check_latency(500)
    assert result is not None
    assert result.is_anomaly
    assert result.severity in ("warning", "critical")


def test_adaptive_detector_no_false_positive():
    d = AdaptiveDetector(min_samples=3, z_threshold_warning=3.0)
    for v in [100, 101, 99, 100, 102]:
        d.observe("latency_ms", v)
    result = d.check_latency(105)
    assert result is None


def test_adaptive_detector_severity_scaling():
    d = AdaptiveDetector(min_samples=3, z_threshold_warning=1.0, z_threshold_critical=2.0)
    for v in [10, 12, 11, 9, 10]:
        d.observe("latency_ms", v)
    result = d.check_latency(100)
    assert result is not None
    assert result.severity == "critical"


def test_adaptive_detector_baseline_summary():
    d = AdaptiveDetector(min_samples=2)
    d.observe("test_metric", 100)
    d.observe("test_metric", 200)
    summary = d.get_baseline_summary()
    assert "test_metric" in summary
    assert summary["test_metric"]["count"] == 2


def test_adaptive_detector_confidence_check():
    d = AdaptiveDetector(min_samples=3, z_threshold_warning=1.0)
    for v in [0.9, 0.85, 0.95]:
        d.observe("confidence", v)
    result = d.check_confidence(0.1)
    assert result is not None
    assert result.is_anomaly


def test_adaptive_detector_issues_check():
    d = AdaptiveDetector(min_samples=1)
    result = d.check_issues(0, 600)
    assert result is not None
    assert result.severity in ("suggestion", "warning", "critical")


# ====== Action Executor Tests ======

def test_healer_tune_llm_params_high_latency():
    h = ActionExecutor()
    result = h.tune_llm_params("high_latency", {"temperature": 0.1, "max_tokens": 2048, "model": "llama3.2:3b"})
    assert result["success"]
    assert result["params"]["max_tokens"] == 1024
    assert result["params"]["temperature"] == 0.2


def test_healer_tune_llm_params_low_confidence():
    h = ActionExecutor()
    result = h.tune_llm_params("low_confidence", {"temperature": 0.1, "max_tokens": 2048, "model": "llama3.2:3b"})
    assert result["success"]
    assert result["params"]["temperature"] == 0.05


def test_healer_unknown_anomaly():
    h = ActionExecutor()
    result = h.tune_llm_params("unknown_type")
    assert result["success"]


def test_healer_apply_fix_high_latency_warning():
    h = ActionExecutor()
    result = h.apply_fix({"type": "high_latency", "severity": "warning"})
    assert result["executed"]
    assert result["action"] == "tune_llm_params"


def test_healer_apply_fix_low_confidence():
    h = ActionExecutor()
    result = h.apply_fix({"type": "low_confidence", "severity": "warning"})
    assert result["executed"]
    assert result["action"] == "tune_llm_params"


def test_healer_apply_fix_service_down():
    h = ActionExecutor()
    result = h.apply_fix({"type": "service_down", "severity": "critical"})
    assert result["executed"]
    assert result["action"] == "restart_container"


def test_healer_get_summary():
    h = ActionExecutor()
    h.tune_llm_params("high_latency")
    h.tune_llm_params("low_confidence")
    summary = h.get_summary()
    assert summary["total_actions"] == 2
    assert summary["successful"] == 2
