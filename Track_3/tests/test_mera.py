import pytest
import time
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import MirrorAgent


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
    save_state({"cycles": [], "reviews": [], "anomalies": [], "fixes": [], "alerts": [], "dashboard_url": "", "status": "test"})
    append_cycle({"cycle": 1, "anomalies": 1, "fixes": 1, "traces": 1, "alerts": 1, "timestamp": time.time()})
    s = get_state()
    assert len(s["cycles"]) == 1
    assert s["cycles"][0]["cycle"] == 1
