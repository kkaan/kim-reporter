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
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 2. Frontend dependencies and dev server

```powershell
cd web
npm install
npm run dev   # Vite dev server with HMR on http://localhost:5173
```

### 3. Backend (in a second terminal)

```powershell
$env:KIM_REPORTER_DEV_FRONTEND = "http://localhost:5173"
python -m kim_app
```

This launches uvicorn + a pywebview window pointing at the Vite dev server so
frontend changes hot-reload without restarting the Python process.

## Production build

```powershell
# 1. Build the React bundle
cd web
npm run build        # outputs to ../kim_app/web_dist/

# 2. Package as a single .exe
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
