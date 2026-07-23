# Screenshots — 5 Total for Submission

| # | File | Status | Size |
|---|------|--------|------|
| 1 | `01_terminal_dashboard.png` | ❌ Need to capture | — |
| 2 | `02_web_dashboard.png` | ✅ Already saved (was 2.png) | 178 KB |
| 3 | `03_improvement_table.png` | ✅ Already saved (was 3.png) | 101 KB |
| 4 | `04_terminal_summary.png` | ❌ Need to capture | — |
| 5 | `05_code_structure.png` | ✅ Already saved (was 5.png) | 349 KB |

## How to Capture (1 & 4)

### Screenshot 1 — `01_terminal_dashboard.png`

**Command:**
```powershell
cd Track_3
python run.py --fast
```

**When to capture:** Wait until **Cycle 2** starts running. Anomalies + improvement metrics should be populated. Capture full terminal window showing all 4 panels with data.

**Expected:** Header shows step text, Main Agent panel (issues + confidence), Mirror Agent panel (traces + anomalies), Anomalies panel (z-score entries), Improvement panel (before/after rows).

### Screenshot 4 — `04_terminal_summary.png`

**Command:**
```powershell
cd Track_3
python run.py --fast
```

**When to capture:** Wait for the demo to finish — a **"Demo Complete"** summary panel appears with a double-line border.

**Expected:** Cycles Completed 3/3, Anomalies Detected 6, Fixes Executed 6, Total Improvement ~152%, Self-Healed Cycles 3/3, SigNoz + Dashboard URLs.

---

## Files That Are Already Saved

| Current Name | Original Name | Size | Content |
|-------------|---------------|------|---------|
| `02_web_dashboard.png` | `2.png` | 178 KB | Web dashboard at http://localhost:9000 |
| `03_improvement_table.png` | `3.png` | 101 KB | Improvement metrics close-up |
| `05_code_structure.png` | `5.png` | 349 KB | VSCode/file explorer folder tree |

---

## Steps After All 5 Captured

```powershell
# Verify all 5 files exist
Get-ChildItem screenshots

# Push to GitHub
git add screenshots/
git commit -m "Add screenshots"
git push
```
