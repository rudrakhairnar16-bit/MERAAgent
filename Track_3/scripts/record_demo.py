"""
MERA Demo Recorder — captures terminal output for demo video reference.

Usage:
    python scripts/record_demo.py

This runs the full MERA pipeline and prints timestamped logs.
Use the output as a script for your demo video recording.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import reset_state
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import run_self_healing_cycle, MirrorAgent

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"

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


def log(msg, style=""):
    ts = time.strftime("%H:%M:%S")
    print(f"{style}[{ts}] {msg}{RESET}")
    time.sleep(0.5)


def main():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  MERA Demo Recording Script{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    input(f"{BOLD}Ready to start recording? Press Enter when your screen recorder is ready...{RESET}")
    print()

    log("Initializing MERA system...", BOLD)
    reset_state()
    agent = PRReviewAgent()
    log(f"Main Agent initialized (model: {agent.model})", GREEN)

    log("\n--- PHASE 1: Main Agent Code Reviews ---", BOLD)
    for i, s in enumerate(SAMPLE_CODES):
        log(f"Reviewing {s['language']} code (sample {i+1}/3)...", CYAN)
        start = time.time()
        r = agent.review_code(s["code"], s["language"])
        elapsed = time.time() - start
        issues = r.get("issues", [])
        confidence = r.get("confidence", 0)
        summary = r.get("summary", "")
        log(f"  Issues found: {len(issues)}", GREEN if issues else YELLOW)
        log(f"  Confidence: {confidence:.2f}", GREEN if confidence > 0.5 else YELLOW)
        log(f"  Latency: {elapsed*1000:.0f}ms", MAGENTA)
        log(f"  Summary: {summary[:80]}", CYAN)
        for issue in issues[:2]:
            log(f"    ⚡ Line {issue.get('line', '?')} [{issue.get('severity','info')}]: {issue.get('message','')[:60]}", YELLOW)

    log("\n--- PHASE 2: Mirror Agent Self-Healing Cycles ---", BOLD)
    for cycle in range(3):
        log(f"Self-Healing Cycle {cycle+1}/3...", BOLD)
        anomalies = run_self_healing_cycle()
        if anomalies:
            for a in anomalies:
                log(f"  ⚠ Anomaly: {a['type']} ({a['severity']})", RED)
                mirror = MirrorAgent()
                fix = mirror.generate_fix_suggestion(a)
                log(f"  ✓ Fix: {fix.get('fix', '')[:60]}", GREEN)
        else:
            log(f"  ✓ System healthy — no anomalies", GREEN)
        time.sleep(2)

    print(f"\n{BOLD}{GREEN}{'='*60}{RESET}")
    log(f"MERA Demo Complete!", BOLD)
    log(f"Check SigNoz: http://localhost:8080", CYAN)
    log(f"Check Dashboard: http://localhost:9000", CYAN)
    print(f"{BOLD}{GREEN}{'='*60}{RESET}\n")

    log("Now show SigNoz traces in your browser...", YELLOW)
    log("1. Open http://localhost:8080 → Traces tab", YELLOW)
    log("2. Filter by service: mera-main-agent", YELLOW)
    log("3. View the instrumented spans (pr_review, llm_call)", YELLOW)
    log("4. Open Dashboards → MERA Dashboard (if imported)", YELLOW)


if __name__ == "__main__":
    main()
