import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="MERA Dashboard", version="2.0.0")

HERE = Path(__file__).parent
templates = Jinja2Templates(directory=str(HERE / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    from state import get_state
    state = get_state()
    return templates.TemplateResponse("dashboard.html", {"request": request, "state": state})


@app.get("/api/status")
async def api_status():
    from state import get_state
    return JSONResponse(get_state())


@app.get("/api/cycles")
async def api_cycles():
    from state import get_state
    return JSONResponse(get_state().get("cycles", []))


@app.get("/api/anomalies")
async def api_anomalies():
    from state import get_state
    return JSONResponse(get_state().get("anomalies", []))


@app.get("/api/fixes")
async def api_fixes():
    from state import get_state
    return JSONResponse(get_state().get("fixes", []))


@app.get("/api/baseline")
async def api_baseline():
    from state import get_state
    return JSONResponse(get_state().get("baseline", {}))


@app.get("/api/improvements")
async def api_improvements():
    from state import get_state
    state = get_state()
    cycles = state.get("cycles", [])
    improvements = [
        {
            "cycle": c.get("cycle"),
            "latency_before": c.get("latency_before", 0),
            "latency_after": c.get("latency_after", 0),
            "improvement_pct": c.get("latency_improvement_pct", 0),
            "self_healed": c.get("self_healed", False)
        }
        for c in cycles if c.get("latency_before") or c.get("latency_after")
    ]
    return JSONResponse(improvements)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MERA_DASHBOARD_PORT", "9000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
