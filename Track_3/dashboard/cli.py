import os
import sys
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.live import Live
    from rich.text import Text
    from rich import box
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from state import get_state, append_cycle, append_review, append_anomalies, append_fixes
from main_agent.agent import PRReviewAgent
from mirror_agent.mirror import run_self_healing_cycle, MirrorAgent

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


class MERATerminalDashboard:
    def __init__(self):
        self.console = Console()
        self.stop_event = threading.Event()
        self.main_agent = PRReviewAgent()
        self.mirror_agent = MirrorAgent()
        self.current_review = {"language": "-", "issues": 0, "confidence": 0, "status": "idle"}
        self.current_cycle = {"num": 0, "traces": 0, "anomalies": 0, "fixes": 0, "status": "waiting"}
        self.anomaly_log = []
        self.fix_log = []
        self.cycle_progress = 0

    def make_layout(self):
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="main_panel", ratio=1),
            Layout(name="mirror_panel", ratio=1),
        )
        layout["body"].split_column(
            Layout(name="top_row", ratio=1),
            Layout(name="bottom_row", ratio=1)
        )
        layout["top_row"].split_row(
            Layout(name="main_panel", ratio=1),
            Layout(name="mirror_panel", ratio=1)
        )
        layout["bottom_row"].split_row(
            Layout(name="anomaly_panel", ratio=1),
            Layout(name="progress_panel", ratio=1)
        )
        return layout

    def render_header(self):
        text = Text()
        text.append(" MERA ", style="bold white on blue")
        text.append(" Mirror Entity Recursive Agent ", style="bold white")
        text.append("  [ Self-Healing AI System ]", style="dim white")
        status = self.current_cycle["status"]
        status_style = "green" if "complete" in status else "yellow" if "running" in status else "dim"
        text.append(f"  [{status}]", style=status_style)
        return Panel(text, box=box.HEAVY, style="blue")

    def render_main_panel(self):
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Key", style="cyan", width=14)
        table.add_column("Value", style="white")
        table.add_row("Status", self.current_review.get("status", "idle"))
        table.add_row("Language", self.current_review.get("language", "-"))
        table.add_row("Issues", str(self.current_review.get("issues", 0)))
        conf = self.current_review.get("confidence", 0)
        conf_str = f"{conf:.2f}"
        conf_style = "green" if conf >= 0.7 else "yellow" if conf >= 0.5 else "red"
        table.add_row("Confidence", f"[{conf_style}]{conf_str}[/]")
        return Panel(table, title="[bold cyan]Main Agent[/] — PR Reviewer", box=box.ROUNDED, border_style="cyan")

    def render_mirror_panel(self):
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column("Key", style="magenta", width=14)
        table.add_column("Value", style="white")
        table.add_row("Cycle", str(self.current_cycle.get("num", 0)))
        table.add_row("Traces", str(self.current_cycle.get("traces", 0)))
        anom = self.current_cycle.get("anomalies", 0)
        anom_style = "green" if anom == 0 else "yellow" if anom <= 3 else "red"
        table.add_row("Anomalies", f"[{anom_style}]{anom}[/]")
        table.add_row("Fixes", str(self.current_cycle.get("fixes", 0)))
        return Panel(table, title="[bold magenta]Mirror Agent[/] — Observer", box=box.ROUNDED, border_style="magenta")

    def render_anomaly_panel(self):
        if not self.anomaly_log:
            return Panel("[dim]No anomalies detected yet[/]", title="[bold yellow]Anomalies[/]", box=box.ROUNDED, border_style="yellow")
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow", padding=(0, 1))
        table.add_column("Type", width=18)
        table.add_column("Severity", width=10)
        table.add_column("Message", width=40)
        for a in self.anomaly_log[-5:]:
            sev_style = {"critical": "red", "warning": "yellow", "suggestion": "blue"}.get(a.get("severity", ""), "white")
            table.add_row(
                a.get("type", ""),
                f"[{sev_style}]{a.get('severity', '')}[/]",
                a.get("message", "")[:38]
            )
        return Panel(table, title="[bold yellow]Recent Anomalies[/]", box=box.ROUNDED, border_style="yellow")

    def render_progress_panel(self):
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )
        task = progress.add_task("[cyan]Self-Healing Cycles", total=3)
        progress.update(task, completed=self.cycle_progress)
        panel = Panel(progress, title="[bold green]Progress[/]", box=box.ROUNDED, border_style="green")
        return panel

    def render_footer(self):
        text = Text()
        text.append(" SigNoz: http://localhost:8080  ", style="blue")
        text.append("|  Dashboard: http://localhost:9000  ", style="cyan")
        text.append("|  Ctrl+C to stop", style="dim")
        return Panel(text, box=box.SIMPLE, style="dim")

    def render(self):
        layout = self.make_layout()
        layout["header"].update(self.render_header())
        layout["main_panel"].update(self.render_main_panel())
        layout["mirror_panel"].update(self.render_mirror_panel())
        layout["anomaly_panel"].update(self.render_anomaly_panel())
        layout["progress_panel"].update(self.render_progress_panel())
        layout["footer"].update(self.render_footer())
        return layout

    def update_review(self, language, issues, confidence, status):
        self.current_review = {
            "language": language,
            "issues": issues,
            "confidence": confidence,
            "status": status
        }

    def update_cycle(self, num, traces=0, anomalies=0, fixes=0, status="running"):
        self.current_cycle = {
            "num": num,
            "traces": traces,
            "anomalies": anomalies,
            "fixes": fixes,
            "status": status
        }
        if status == "complete":
            self.cycle_progress = num

    def add_anomaly(self, anomaly):
        self.anomaly_log.append(anomaly)

    def add_fix(self, fix):
        self.fix_log.append(fix)

    def run(self):
        with Live(self.render(), refresh_per_second=4, screen=True) as live:
            self.update_review("-", 0, 0, "starting...")
            live.update(self.render())

            for i in range(3):
                s = SAMPLE_CODES[i % len(SAMPLE_CODES)]
                self.update_cycle(i + 1, status=f"reviewing {s['language']}...")
                self.update_review(s["language"], 0, 0, "reviewing...")
                live.update(self.render())

                try:
                    r = self.main_agent.review_code(s["code"], s["language"])
                    issues = len(r.get("issues", []))
                    confidence = r.get("confidence", 0)
                    self.update_review(s["language"], issues, confidence, "done")
                    append_review({
                        "cycle": i, "language": s["language"],
                        "issues_count": issues, "confidence": confidence,
                        "summary": r.get("summary", ""), "timestamp": time.time()
                    })
                except Exception as e:
                    self.update_review(s["language"], 0, 0, f"error: {e}")
                live.update(self.render())
                time.sleep(2)

                self.update_cycle(i + 1, status="mirror cycle...")
                live.update(self.render())

                try:
                    anomalies = run_self_healing_cycle()
                    if anomalies:
                        append_anomalies(anomalies)
                        for a in anomalies:
                            self.add_anomaly(a)
                        fixes = []
                        for a in anomalies:
                            fix = self.mirror_agent.generate_fix_suggestion(a)
                            fixes.append(fix)
                            self.add_fix(fix)
                        append_fixes(fixes)
                    self.update_cycle(
                        i + 1,
                        traces=len(anomalies or []),
                        anomalies=len(anomalies or []),
                        fixes=len(anomalies or []),
                        status="complete"
                    )
                    append_cycle({
                        "cycle": i + 1, "anomalies": len(anomalies or []),
                        "fixes": len(anomalies or []), "traces": len(anomalies or []),
                        "alerts": 0, "timestamp": time.time()
                    })
                except Exception as e:
                    self.update_cycle(i + 1, status=f"error: {e}")
                live.update(self.render())
                time.sleep(3)

            live.update(self.render())
            time.sleep(2)

            from rich.panel import Panel as RPanel
            from rich.text import Text as RText
            from rich import box as RBox

            summary = Table(box=RBox.HEAVY, show_header=False, padding=(1, 2))
            summary.add_column("Metric", style="bold cyan")
            summary.add_column("Value", style="bold white")
            summary.add_row("Cycles Completed", "3/3")
            summary.add_row("Anomalies Detected", str(len(self.anomaly_log)))
            summary.add_row("Fixes Generated", str(len(self.fix_log)))
            summary.add_row("SigNoz", "http://localhost:8080")
            summary.add_row("Dashboard", "http://localhost:9000")

            live.update(Panel(summary, title="[bold green] Demo Complete [/]", box=RBox.DOUBLE, border_style="green"))
            time.sleep(5)


def run_dashboard():
    if not HAS_RICH:
        print("=" * 55)
        print("  MERA - Mirror Entity Recursive Agent")
        print("  Self-Healing AI System with SigNoz")
        print("=" * 55)
        print("\n  Install rich for the live terminal dashboard:")
        print("  pip install rich\n")
        from run import main as run_simple
        run_simple()
        return

    dashboard = MERATerminalDashboard()
    try:
        dashboard.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_dashboard()
