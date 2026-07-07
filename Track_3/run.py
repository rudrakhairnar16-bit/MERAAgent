import os
import sys
import time
import json
import threading
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import run_self_healing_cycle
from state import append_cycle, append_review, append_anomalies, append_fixes, update_alerts

load_dotenv()

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


def run_main_agent_loop(agent, stop):
    cycle = 0
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
        for _ in range(30):
            if stop.is_set():
                return
            time.sleep(0.1)


def main():
    print("=" * 55)
    print("  MERA - Mirror Entity Recursive Agent")
    print("  Self-Healing AI System with SigNoz")
    print("=" * 55)

    agent = PRReviewAgent()
    stop = threading.Event()

    t = threading.Thread(target=run_main_agent_loop, args=(agent, stop), daemon=True)
    t.start()

    print("\n[System] Main agent started. Waiting 5s before first mirror cycle...\n")
    time.sleep(5)

    for i in range(3):
        print(f"\n{'='*55}\n  Self-Healing Cycle {i+1}/3\n{'='*55}")
        try:
            anomalies = run_self_healing_cycle()
            if anomalies:
                append_anomalies(anomalies)
                fixes = []
                from mirror_agent.mirror import MirrorAgent
                m = MirrorAgent()
                for a in anomalies:
                    fix = m.generate_fix_suggestion(a)
                    fixes.append(fix)
                append_fixes(fixes)
                print(f"  {len(fixes)} fixes generated")
            else:
                print("  System healthy - no anomalies")
            append_cycle({
                "cycle": i + 1,
                "anomalies": len(anomalies or []),
                "fixes": len(anomalies or []),
                "traces": len(anomalies or []),
                "alerts": 0,
                "timestamp": time.time()
            })
        except Exception as e:
            print(f"  Cycle error: {e}")
            append_cycle({"cycle": i + 1, "error": str(e), "timestamp": time.time()})
        time.sleep(8)

    stop.set()
    print("\n" + "=" * 55)
    print("  Demo Complete - 3 Cycles Executed")
    print("  Dashboard: http://localhost:9000")
    print("  SigNoz:    http://localhost:8080")
    print("=" * 55)


if __name__ == "__main__":
    main()
