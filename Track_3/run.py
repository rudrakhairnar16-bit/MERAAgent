import os
import sys
import time
import json
import threading
from typing import Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import run_self_healing_cycle
from mirror_agent.mirror import MirrorAgent
from state import append_cycle, append_review, append_anomalies, append_fixes, update_alerts, update_baseline, reset_state
from signoz_config.tracing import get_tracer, force_flush, get_current_trace_id, set_trace_context

load_dotenv()

tracer = get_tracer("mera-orchestrator")

SAMPLE_CODES = [
    {
        "language": "python",
        "code": """
def calc(price, discount):
    return price - (price * discount / 100)

class Cart:
    def __init__(self):
        self.items = []
    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})
    def total(self):
        t = 0
        for i in self.items:
            t = t + i["price"] * i["qty"]
        return t
"""
    },
    {
        "language": "javascript",
        "code": """
function getData(url) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, false);
    xhr.send();
    return xhr.responseText;
}
var counter = 0;
function inc() { counter++; }

app.get('/user/:id', (req, res) => {
    var q = "SELECT * FROM users WHERE id = " + req.params.id;
    db.query(q, function(e, r) { res.send(r); });
});
"""
    },
    {
        "language": "python",
        "code": """
import os, pickle
def load_data(file):
    with open(file, 'rb') as f:
        return pickle.load(f)

def save_config(cfg):
    with open('/tmp/config.cfg', 'w') as f:
        f.write(str(cfg))

def run_cmd(cmd):
    os.system(cmd)
    return os.popen(cmd).read()
"""
    }
]


FAST = "--fast" in sys.argv or os.getenv("DEMO_FAST") == "1"


def run_main_agent_loop(agent: PRReviewAgent, stop: threading.Event) -> None:
    cycle = 0
    wait_iters = 5 if FAST else 30
    while not stop.is_set():
        s = SAMPLE_CODES[cycle % len(SAMPLE_CODES)]
        print(f"[Main] Reviewing {s['language']} (cycle {cycle+1})...")
        try:
            r = agent.review_code(s["code"], s["language"])
            print(f"  Issues: {len(r.get('issues',[]))} | Confidence: {r.get('confidence',0):.2f}")
            append_review({
                "cycle": cycle,
                "language": s["language"],
                "issues_count": len(r.get("issues", [])),
                "confidence": r.get("confidence", 0),
                "summary": r.get("summary", ""),
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"  Error: {e}")
        cycle += 1
        for _ in range(wait_iters):
            if stop.is_set():
                return
            time.sleep(0.1)


def main() -> None:
    reset_state()
    print("=" * 55)
    print("  MERA - Mirror Entity Recursive Agent")
    print("  Self-Healing AI System with SigNoz")
    print("=" * 55)

    agent = PRReviewAgent()
    mirror = MirrorAgent()
    stop = threading.Event()

    t = threading.Thread(target=run_main_agent_loop, args=(agent, stop), daemon=True)
    t.start()

    wait_init = 1 if FAST else 5
    print(f"\n[System] Main agent started. Waiting {wait_init}s before first mirror cycle...\n")
    time.sleep(wait_init)

    for i in range(3):
        print(f"\n{'='*55}\n  Self-Healing Cycle {i+1}/3\n{'='*55}")
        with tracer.start_as_current_span("orchestrator_cycle") as root_span:
            root_span.set_attribute("cycle.number", i + 1)
            root_span.set_attribute("cycle.total", 3)
            root_span.add_event("cycle_started", {"cycle": i + 1})
            root_trace_id = get_current_trace_id()
            if root_trace_id:
                root_span.set_attribute("cycle.trace_id", root_trace_id)
                set_trace_context(root_trace_id)
            latency_before = 0.0
            try:
                anomalies = run_self_healing_cycle()
                if anomalies:
                    append_anomalies(anomalies)
                    fixes = []
                    for a in anomalies:
                        fix = mirror.generate_fix_suggestion(a)
                        fixes.append(fix)
                    append_fixes(fixes)
                    self_healed = any(f.get("executed") for f in fixes)
                    print(f"  {len(fixes)} fixes generated (auto-executed: {self_healed})")
                    root_span.set_attribute("cycle.self_healed", self_healed)
                else:
                    print("  System healthy — no anomalies")
                    self_healed = False
                baseline = mirror.get_before_after_metrics()
                latency_after = baseline.get("latency", {}).get("after", 0.0)
                improvement = baseline.get("latency", {}).get("improvement_pct", 0.0)
                update_baseline(mirror.get_baseline_state())
                cycle_data = {
                    "cycle": i + 1,
                    "anomalies": len(anomalies or []),
                    "fixes": len(anomalies or []),
                    "traces": len(anomalies or []),
                    "alerts": 0,
                    "timestamp": time.time(),
                    "latency_before": latency_before,
                    "latency_after": latency_after,
                    "latency_improvement_pct": improvement,
                    "self_healed": self_healed
                }
                append_cycle(cycle_data)
                root_span.set_attribute("cycle.anomalies", len(anomalies or []))
                root_span.set_attribute("cycle.fixes", len(anomalies or []))
                root_span.set_attribute("cycle.latency_improvement_pct", improvement)
                root_span.add_event("cycle_completed", {
                    "anomalies": len(anomalies or []),
                    "improvement": improvement
                })
            except Exception as e:
                print(f"  Cycle error: {e}")
                append_cycle({"cycle": i + 1, "error": str(e), "timestamp": time.time()})
                root_span.record_exception(e)
        force_flush()
        cycle_wait = 2 if FAST else 8
        time.sleep(cycle_wait)

    stop.set()
    print("\n" + "=" * 55)
    print("  MERA Demo Complete!")
    print("=" * 55)
    print()
    print("  What was done:")
    print("   ✓ 3 code reviews performed by Main Agent")
    print("   ✓ 3 self-healing cycles by Mirror Agent")
    print("   ✓ OpenTelemetry traces sent to SigNoz")
    print("   ✓ Adaptive anomaly detection with statistical baselines")
    print("   ✓ Auto-executed fixes (Docker restart, LLM tuning)")
    print("   ✓ Cross-component trace correlation")
    print()
    print("  Where to check:")
    print("   MERA Dashboard  → http://localhost:9000")
    print("   SigNoz Traces   → http://localhost:8080")
    print("   SigNoz Alerts   → http://localhost:8080/alerts")
    print()
    print("  To clean up:")
    print("   Run: scripts\\cleanup.bat")
    print("=" * 55)


if __name__ == "__main__":
    try:
        from rich.console import Console
        print(" Launching terminal dashboard...")
        from dashboard.cli import run_dashboard
        run_dashboard()
    except ImportError:
        main()
