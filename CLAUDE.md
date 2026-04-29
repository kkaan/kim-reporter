# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Desktop app for medical physicists to inspect KIM-guided couch corrections from PRIME trajectory logs and export clinical PDF reports. Single Python process: FastAPI/uvicorn runs in a daemon thread, pywebview (Edge WebView2) hosts the React frontend on the main thread. All communication is localhost REST.

## Commands

### Development

```powershell
# Backend (terminal 1) — starts FastAPI server + pywebview window
$env:KIM_REPORTER_DEV_FRONTEND = "http://localhost:5173"
python -m kim_app

# Frontend (terminal 2)
cd web
npm install        # once, or after package.json changes
npm run dev        # Vite dev server at http://localhost:5173, proxies /api to :8765
```

### Type-check / lint

```powershell
cd web && npx tsc --noEmit    # frontend type-check (also runs as part of npm run build)
```

No Python linter or formatter is configured in the repo.

### Tests

```powershell
pytest              # from repo root, with .venv activated
```

No test files exist yet — `[dev]` optional deps include pytest.

### Production build

```powershell
cd web && npm run build              # outputs to kim_app/web_dist/
cd .. && pyinstaller KIM-QA-Reporter.spec   # outputs dist/KIM-QA-Reporter.exe
```

## Architecture

**Backend** (`kim_app/`): Python 3.11+, FastAPI, Pydantic v2. Entrypoint is `__main__.py` which starts uvicorn in a daemon thread, then opens a pywebview window. The `KIM_REPORTER_DEV_FRONTEND` env var switches the window URL to the Vite dev server for hot-reload.

**Frontend** (`web/`): React 18, TypeScript, Vite, Tailwind CSS, react-plotly.js, Zustand for state. Built into `kim_app/web_dist/` (git-ignored) so the Python package serves it as static files. In dev, Vite proxies `/api/*` to the backend at `:8765`.

**API surface** (`kim_app/api/routes.py`): Three main endpoints:
- `POST /api/scan` — index a patient directory, find centroid file, list fractions
- `POST /api/fraction` — load one fraction's deviation timeseries
- `POST /api/render-pdf` — produce A4 clinical PDF

**Core parsing** (`kim_app/core/`):
- `loader.py` — trajectory file reader with sentinel/glitch filtering and dynamic 1–N marker support. Axis swap: x=LR, y=SI, z=−AP (from MATLAB Staticloc.m convention).
- `shifts.py` — `couchShifts.txt` parser. Handles FX01 merged-session anomaly (stale leading rows). VRT→AP, LNG→SI, LAT→LR.
- `window.py` — beam-off gap compression for display time axis. Pure functions, no matplotlib.
- `overlay.py` — no-correction counterfactual: subtracts applied shift from post-correction trace.

**PDF** (`kim_app/pdf/report.py`): matplotlib-rendered deviation plots embedded as PNGs in a ReportLab A4 document. Uses `matplotlib.use("Agg")` — no display backend.

**Wire contract**: all times are seconds (float), distances are mm (float), couch positions are cm (float, VRT/LNG/LAT triple). Defined in `kim_app/api/schema.py`.

## Key domain quirks

- Trajectory files (`MarkerLocationsGA_CouchShift_*.txt`): only file 0 has a header; continuation files are headerless. Time field has thousands-separator commas after 1000 s (e.g. `"1,000.305"`).
- Sentinel frames (~135 mm) are pre-tracking-lock placeholders — filtered by `SANE_LIMIT_MM = 50`.
- Glitch filter thresholds differ per axis: LR ±5 mm, SI/AP ±12 mm.
- FX01 `couchShifts.txt` may contain two recording sessions concatenated with a repeated header mid-file. The `couch_row_count` parameter trims stale leading rows.
- Frontend discovers the backend URL via `?api=...` query param (injected by pywebview in dev) or same-origin in production.

## Environment variables

- `KIM_REPORTER_DEV_FRONTEND` — Vite dev server URL (e.g. `http://localhost:5173`). Enables CORS, switches pywebview URL.
- `KIM_REPORTER_LOG_LEVEL` — uvicorn log level (default: `warning`).
- `KIM_REPORTER_DEBUG` — enables pywebview debug mode (DevTools in WebView2 window).
