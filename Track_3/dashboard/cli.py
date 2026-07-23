import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HAS_RICH = False
try:
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    pass

from state import append_cycle, append_review, append_anomalies, append_fixes, reset_state

FAST = "--fast" in sys.argv or os.getenv("DEMO_FAST") == "1"


def _mock_review(language):
    issues_by_lang = {
        "python": [
            {"line": 5, "severity": "warning", "message": "Unused variable `discount` may indicate logic error", "suggestion": "Verify discount parameter is intentional"},
            {"line": 12, "severity": "warning", "message": "Mutable default argument `[]` shared across calls", "suggestion": "Use None and initialize inside method"},
            {"line": 18, "severity": "suggestion", "message": "Use sum() with generator for readability", "suggestion": "return sum(i['price'] * i['qty'] for i in self.items)"},
        ],
        "javascript": [
            {"line": 3, "severity": "error", "message": "Synchronous XMLHttpRequest blocks main thread", "suggestion": "Use fetch() with async/await"},
            {"line": 12, "severity": "error", "message": "SQL injection via string concatenation", "suggestion": "Use parameterized queries"},
            {"line": 7, "severity": "warning", "message": "Global mutable state `counter` is not thread-safe", "suggestion": "Encapsulate in a closure or class"},
        ],
    }
    issues = issues_by_lang.get(language, issues_by_lang["python"])
    return {
        "issues": issues,
        "confidence": 0.82,
        "summary": f"Found {len(issues)} issues in {language} code"
    }


def _generate_cycle_data(cycle_num):
    latency_before = random.uniform(800, 5000)
    latency_after = latency_before * random.uniform(0.3, 0.7)
    improvement = ((latency_before - latency_after) / latency_before) * 100
    return {
        "latency_before": latency_before,
        "latency_after": latency_after,
        "improvement_pct": improvement,
        "self_healed": True,
        "anomalies": [
            {
                "type": "latency",
                "severity": "warning",
                "z_score": 2.5,
                "message": f"High latency detected: {latency_before:.0f}ms (z=2.5)"
            },
            {
                "type": "cpu",
                "severity": "suggestion",
                "z_score": 1.8,
                "message": "Elevated CPU usage in LLM call handler"
            }
        ]
    }


def run_demo(fast):
    reset_state()
    print("=" * 55)
    print("  MERA - Mirror Entity Recursive Agent")
    print("  Self-Healing AI System with SigNoz")
    print("  [DEMO MODE - Simulated Data]")
    print("=" * 55)

    if not HAS_RICH:
        print("\n  Install rich for the live dashboard:")
        print("  pip install rich\n")
        return

    dashboard = MERATerminalDashboard()
    try:
        dashboard.run(fast)
    except KeyboardInterrupt:
        pass


class MERATerminalDashboard:
    def __init__(self):
        self.cycle_data = []
        self.review_done = False
        self.step = ""
        self.cycle_num = 0
        self.review_status = "waiting"
        self.issues_count = 0
        self.confidence = 0.0
        self.lang = "-"
        self.traces = 0
        self.anomalies = 0
        self.fixes = 0
        self.healed = False
        self.improvement = 0.0
        self.anomaly_details = []

    def make_layout(self):
        layout = Layout()
        layout.split(
            Layout(name="header", size=4),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
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
            Layout(name="improvement_panel", ratio=1)
        )
        return layout

    def render(self):
        layout = self.make_layout()

        h = Text()
        h.append(" MERA ", style="bold white on blue")
        h.append(" Mirror Entity Recursive Agent ", style="bold white")
        if self.step:
            h.append(f"\n  {self.step}", style="bold white on grey35")
        layout["header"].update(Panel(h, box=box.HEAVY, style="blue"))

        mt = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        mt.add_column("Key", style="cyan", width=16)
        mt.add_column("Value", style="white")
        mt.add_row("Status", self.review_status)
        mt.add_row("Language", self.lang)
        mt.add_row("Issues", str(self.issues_count))
        cs = f"{self.confidence:.2f}"
        cs_st = "green" if self.confidence >= 0.7 else "yellow" if self.confidence >= 0.5 else "red"
        mt.add_row("Confidence", f"[{cs_st}]{cs}[/]")
        layout["main_panel"].update(Panel(mt, title="[bold cyan]Main Agent[/] — PR Reviewer", box=box.ROUNDED, border_style="cyan"))

        mrt = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        mrt.add_column("Key", style="magenta", width=16)
        mrt.add_column("Value", style="white")
        mrt.add_row("Cycle", str(self.cycle_num))
        mrt.add_row("Traces", str(self.traces))
        ao = "green" if self.anomalies == 0 else "yellow" if self.anomalies <= 3 else "red"
        mrt.add_row("Anomalies", f"[{ao}]{self.anomalies}[/]")
        mrt.add_row("Fixes", str(self.fixes))
        hl = "Y" if self.healed else "N"
        hs = "green" if self.healed else "dim"
        mrt.add_row("Self-Healed", f"[{hs}]{hl}[/]")
        layout["mirror_panel"].update(Panel(mrt, title="[bold magenta]Mirror Agent[/] — Observer + Healer", box=box.ROUNDED, border_style="magenta"))

        if not self.anomaly_details:
            layout["anomaly_panel"].update(Panel("[dim]No anomalies detected yet[/]", title="[bold yellow]Anomalies[/]", box=box.ROUNDED, border_style="yellow"))
        else:
            at = Table(box=box.SIMPLE, show_header=True, header_style="bold yellow", padding=(0, 1))
            at.add_column("Type", width=16)
            at.add_column("Severity", width=10)
            at.add_column("Z-Score", width=8)
            at.add_column("Message", width=38)
            for a in self.anomaly_details[-6:]:
                sev_st = {"critical": "red", "warning": "yellow", "suggestion": "blue"}.get(a.get("severity", ""), "white")
                z = a.get("z_score", "")
                zs = f"{z:.1f}" if isinstance(z, (int, float)) else "-"
                at.add_row(a.get("type", ""), f"[{sev_st}]{a.get('severity', '')}[/]", zs, a.get("message", "")[:36])
            layout["anomaly_panel"].update(Panel(at, title="[bold yellow]Adaptive Anomaly Detection (Z-Score)[/]", box=box.ROUNDED, border_style="yellow"))

        if not self.cycle_data:
            layout["improvement_panel"].update(Panel("[dim]Waiting for cycle data...[/]", title="[bold green]Improvement Metrics[/]", box=box.ROUNDED, border_style="green"))
        else:
            it = Table(box=box.SIMPLE, show_header=True, header_style="bold green", padding=(0, 1))
            it.add_column("Cycle", width=6)
            it.add_column("Before", width=14)
            it.add_column("After", width=13)
            it.add_column("Improvement", width=14)
            it.add_column("Healed", width=8)
            for imp in self.cycle_data[-5:]:
                pct = imp.get("improvement_pct", 0)
                ps = "green" if pct > 0 else "dim"
                ps_s = f"[{ps}]{pct:+.1f}%[/]" if pct else "-"
                hl = "Y" if imp.get("self_healed") else "N"
                hs = "green" if imp.get("self_healed") else "dim"
                it.add_row(str(imp.get("cycle", "")), f"{imp.get('latency_before', 0):.0f}ms", f"{imp.get('latency_after', 0):.0f}ms", ps_s, f"[{hs}]{hl}[/]")
            layout["improvement_panel"].update(Panel(it, title="[bold green]Before / After Metrics[/]", box=box.ROUNDED, border_style="green"))

        ft = Text()
        ft.append(" SigNoz: http://localhost:8080  ", style="blue")
        ft.append("|  Dashboard: http://localhost:9000  ", style="cyan")
        ft.append("|  Ctrl+C to stop", style="dim")
        layout["footer"].update(Panel(ft, box=box.SIMPLE, style="dim"))

        return layout

    def run(self, fast=False):
        sleep_short = 0.3 if fast else 2
        sleep_long = 0.5 if fast else 3

        with Live(self.render(), refresh_per_second=4, screen=True) as live:
            for i in range(3):
                langs = ["python", "javascript", "python"]
                lang = langs[i]

                self.cycle_num = i + 1
                self.lang = lang
                self.review_status = "reviewing..."
                self.step = f"[{i+1}/3] Reviewing {lang} code with LLM..."
                live.update(self.render())
                time.sleep(sleep_short)

                review = _mock_review(lang)
                self.issues_count = len(review.get("issues", []))
                self.confidence = review.get("confidence", 0.82)
                self.review_status = "done"
                self.step = f"[{i+1}/3] Review complete — {self.issues_count} issues found"
                append_review({
                    "cycle": i, "language": lang,
                    "issues_count": self.issues_count, "confidence": self.confidence,
                    "summary": review.get("summary", ""), "timestamp": time.time()
                })
                live.update(self.render())
                time.sleep(sleep_short)

                self.step = f"[{i+1}/3] Mirror agent analyzing traces..."
                live.update(self.render())
                time.sleep(sleep_short)

                cd = _generate_cycle_data(i + 1)
                self.anomaly_details = cd["anomalies"]
                self.traces = 12
                self.anomalies = len(cd["anomalies"])
                self.fixes = self.anomalies
                self.healed = True
                self.improvement = cd["improvement_pct"]

                append_anomalies(cd["anomalies"])
                fixes_payload = [
                    {"anomaly_type": a["type"], "action": "tune_llm_params", "priority": "high",
                     "fix": f"Applied fix for {a['type']}", "executed": True, "success": True}
                    for a in cd["anomalies"]
                ]
                append_fixes(fixes_payload)

                self.step = f"[{i+1}/3] Anomalies detected! Applying self-healing fixes..."
                live.update(self.render())
                time.sleep(sleep_short)

                self.step = f"[{i+1}/3] Self-healing applied — latency improved by {cd['improvement_pct']:.1f}%"
                self.cycle_data.append({
                    "cycle": i + 1,
                    "latency_before": cd["latency_before"],
                    "latency_after": cd["latency_after"],
                    "improvement_pct": cd["improvement_pct"],
                    "self_healed": True
                })
                append_cycle({
                    "cycle": i + 1, "anomalies": self.anomalies,
                    "fixes": self.fixes, "traces": self.traces,
                    "alerts": 0, "timestamp": time.time(),
                    "latency_before": cd["latency_before"],
                    "latency_after": cd["latency_after"],
                    "latency_improvement_pct": cd["improvement_pct"],
                    "self_healed": True
                })
                live.update(self.render())
                time.sleep(sleep_long)

            total_imp = sum(abs(d.get("improvement_pct", 0)) for d in self.cycle_data)
            from rich.panel import Panel as RPanel
            summary = Table(box=box.HEAVY, show_header=False, padding=(1, 2))
            summary.add_column("Metric", style="bold cyan")
            summary.add_column("Value", style="bold white")
            summary.add_row("Cycles Completed", "3/3")
            summary.add_row("Anomalies Detected", str(len(self.anomaly_details)))
            summary.add_row("Fixes Executed", str(len(self.anomaly_details)))
            summary.add_row("Total Improvement", f"{total_imp:.1f}%")
            summary.add_row("Self-Healed Cycles", "3/3")
            summary.add_row("SigNoz", "http://localhost:8080")
            summary.add_row("Dashboard", "http://localhost:9000")
            live.update(Panel(summary, title="[bold green] Demo Complete [/]", box=box.DOUBLE, border_style="green"))
            time.sleep(5)


def run_dashboard():
    if not HAS_RICH:
        print("=" * 55)
        print("  MERA - Mirror Entity Recursive Agent")
        print("  Self-Healing AI System with SigNoz")
        print("=" * 55)
        print("\n  Install rich for live dashboard: pip install rich\n")
        return
    run_demo(FAST)


if __name__ == "__main__":
    run_dashboard()
