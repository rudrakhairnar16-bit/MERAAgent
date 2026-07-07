import pytest
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import MirrorAgent


def test_main_agent_output_format():
    agent = PRReviewAgent()
    r = agent.review_code("x=1", "python")
    assert "issues" in r and "confidence" in r and "summary" in r


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
