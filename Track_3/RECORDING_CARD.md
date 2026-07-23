# Recording Reference Card — Keep Open While Recording

## Commands
```
cd Track_3
python run.py --fast            # Mock demo (5 sec, no SigNoz needed)
python run.py                    # Real demo (2 min, SigNoz must be running)
foundryctl cast -f casting.yaml  # Start SigNoz
python scripts/setup_api_key.py  # Generate API key
python dashboard/app.py          # Web dashboard (port 9000)
```

## Scene Timings

| Scene | Time | What | Command |
|-------|------|------|---------|
| 1 Hook | 0-12s | Terminal running, text overlay | `python run.py --fast` |
| 2 Architecture | 12-35s | Code tour / file tree | VSCode |
| 3 Live Demo | 35-75s | 3 cycles executing | `python run.py --fast` (edit: speed up 2-3x) |
| 4 SigNoz | 75-100s | Traces in browser | http://localhost:8080 |
| 5 Dashboard | 100-120s | Metrics panel | Terminal summary |
| 6 Closing | 120-130s | GitHub + fade | https://github.com/rudrakhairnar16-bit/MERAAgent |

## Text Overlays
```
Scene 1: "MERA — The Agent That Sees Itself"
Scene 2: "3 Components. 1 Self-Healing Loop."
Scene 3: "Anomaly Detected → Auto-Healed"
Scene 4: "Full Observability — Every Span, Every Attribute"
Scene 5: "Before vs After — Proven Improvement"
Scene 6: (end card) MERA + GitHub + #AgentsOfSigNoz
```

## Audio
- Music: -18dB background
- Track suggestion: "Neon" by SLPSTRM (Uppbeat), "Future Technology" (Pixabay)
- Fade out: last 2 seconds

## Screenshots (after video, before submission)
```
python run.py --fast
# Capture at cycle 3 → 5 screenshots
# Save to Track_3/screenshots/
```

## Checklist
- [ ] 27 tests pass: `pytest tests/ -v -m "not llm"`
- [ ] Screenshots in `Track_3/screenshots/`
- [ ] YouTube video Unlisted
- [ ] Repo URL + Video link + Blog link ready
- [ ] Submit at https://forms.gle/wf9tFYcksrk6P4Zy8
