# KIM-QA Reporter

Desktop application for medical physicists to inspect KIM-guided couch corrections
and export clinical PDF reports for patient documentation.

The app reads a patient directory containing the centroid (seed/iso) file plus
per-fraction trajectory logs (`MarkerLocationsGA_CouchShift_*.txt`) and
`couchShifts.txt`, renders an interactive deviation plot with pan/zoom, and
exports an A4 PDF with the trajectory plots, intervention summary table, and a
free-text physicist-notes section.

## Requirements

- **Python 3.11+**
- **Node.js 18+** (only needed to build the frontend; not required at runtime)
- **Edge WebView2 runtime** — pre-installed on Windows 10 21H2+ and Windows 11.
  If missing on older Windows 10, download the Evergreen installer from
  [Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/).

## Quick start (development)

### 1. Python environment

```powershell
# Create an isolated Python environment so dependencies don't clash with
# other projects on your machine.
python -m venv .venv

# Activate the environment (required each time you open a new terminal).
.venv\Scripts\Activate.ps1

# Install the kim_app package in editable mode, plus dev tools
# (pytest, pyinstaller). Editable mode means Python picks up code changes
# immediately without a reinstall step.
pip install -e ".[dev]"
```

### 2. Backend

```powershell
# Tell the Python app to load the frontend from the Vite dev server instead
# of the bundled web_dist/ folder. Without this, the app serves the last
# production build (or fails if web_dist/ doesn't exist yet).
$env:KIM_REPORTER_DEV_FRONTEND = "http://localhost:5173"

# Start the FastAPI/uvicorn server and open the pywebview desktop window.
# The backend listens on http://127.0.0.1:8765 by default.
python -m kim_app
```

### 3. Frontend dev server (in a second terminal)

```powershell
# Switch into the React app directory.
cd web

# Download all JavaScript dependencies declared in package.json into node_modules/.
# Only needed once (or after package.json changes).
npm install

# Start the Vite development server. Serves the React app at
# http://localhost:5173 with hot-module replacement (HMR) — edits to .tsx
# files appear in the browser without a full page reload.
# Vite proxies /api/* to the Python backend at http://127.0.0.1:8765,
# so opening http://localhost:5173 in a browser also works.
npm run dev
```

The pywebview window opened by `python -m kim_app` points at the Vite dev
server, so frontend edits hot-reload without restarting Python. You can also
open `http://localhost:5173` in a regular browser for DevTools access.

## Production build

```powershell
# Step 1 — compile the React app into static HTML/JS/CSS.
# Vite bundles everything and writes the output to kim_app/web_dist/ so
# PyInstaller can include it in the exe.
cd web
npm run build

# Step 2 — package everything into a single Windows executable.
# PyInstaller reads KIM-QA-Reporter.spec, which tells it to bundle:
#   - the kim_app Python package
#   - the web_dist/ static assets
#   - matplotlib font data
#   - all transitive dependencies (uvicorn, FastAPI, ReportLab, pandas, …)
# The --onefile mode compresses everything into dist/KIM-QA-Reporter.exe.
cd ..
pyinstaller KIM-QA-Reporter.spec
# Output: dist/KIM-QA-Reporter.exe
```

The resulting exe is self-contained: it embeds the FastAPI server, the
compiled React frontend, matplotlib, and ReportLab. Edge WebView2 must be
present on the target machine (it is not bundled).

## Architecture

```
kim-reporter/
├── pyproject.toml
├── KIM-QA-Reporter.spec        # PyInstaller single-file build
├── kim_app/
│   ├── __main__.py             # entrypoint: uvicorn thread + pywebview window
│   ├── server.py               # FastAPI app factory
│   ├── core/
│   │   ├── loader.py           # centroid file parser + dynamic-marker loader
│   │   ├── shifts.py           # couchShifts.txt parsing
│   │   ├── window.py           # beam-off gap compression
│   │   └── overlay.py          # no-correction counterfactual
│   ├── api/
│   │   ├── schema.py           # Pydantic request/response models
│   │   └── routes.py           # /api/scan  /api/fraction  /api/render-pdf
│   ├── pdf/
│   │   └── report.py           # ReportLab A4 clinical template
│   └── web_dist/               # populated by `npm run build` (git-ignored)
└── web/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── src/                    # React 18 + TypeScript + Plotly frontend
```

### Backend (`kim_app/`)

Python + FastAPI. All parsing logic is self-contained:

- `kim_app.core.loader` — parses `Centroid_*.txt` files (seeds + isocenter),
  dynamically detects 1–N implanted markers per fraction, applies the
  sentinel/glitch filters from the PRIME trajectory-log pipeline, and computes
  the centroid deviation timeseries.
- `kim_app.core.shifts` — reads `couchShifts.txt`, handles the FX01
  merged-session anomaly (stale leading rows), converts VRT/LNG/LAT → AP/SI/LR.
- `kim_app.core.window` — compresses beam-off pauses on the display time axis.
- `kim_app.core.overlay` — computes the no-correction counterfactual overlay.

### Frontend (`web/`)

React 18 + TypeScript + Vite + Tailwind CSS + react-plotly.js. Built once with
Vite into `kim_app/web_dist/` and shipped as static assets inside the exe.

### Shell

pywebview (Edge WebView2 on Windows) hosts the React app pointing at the
in-process FastAPI/uvicorn server.

### PDF

ReportLab with matplotlib-rendered figures embedded as PNGs. Produces an A4
portrait report with deviation plots per axis, an intervention summary table,
and a free-text physicist-notes section.

## Input data layout

The app expects a patient directory in this shape:

```
<patient_dir>/
├── Centroid_<PatientID>_BeamID_*.txt   # seed/isocenter file (can be in parent dir)
├── FX01/
│   └── Trajectory Logs/
│       ├── MarkerLocationsGA_CouchShift_0.txt
│       ├── MarkerLocationsGA_CouchShift_1.txt
│       └── couchShifts.txt
├── FX02/
│   └── Trajectory Logs/
│       └── ...
└── ...
```

The centroid file is searched first inside `<patient_dir>`, then in its parent,
so both flat layouts (centroid alongside fraction folders) and nested layouts
(centroid one level up) are handled automatically.
