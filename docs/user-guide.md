# KIM-QA Reporter — User Guide

Desktop application for reviewing KIM-guided couch corrections and exporting
clinical PDF reports from PRIME trajectory logs.

---

## Contents

1. [System requirements](#1-system-requirements)
2. [Launching the application](#2-launching-the-application)
3. [Data folder layout](#3-data-folder-layout)
4. [Loading a patient](#4-loading-a-patient)
5. [Selecting a fraction](#5-selecting-a-fraction)
6. [Reading the deviation plot](#6-reading-the-deviation-plot)
7. [Managing active markers](#7-managing-active-markers)
8. [Fixing the FX01 couch-row anomaly](#8-fixing-the-fx01-couch-row-anomaly)
9. [Adding a manual intervention](#9-adding-a-manual-intervention)
10. [Adjusting highlight bands](#10-adjusting-highlight-bands)
11. [Physicist notes](#11-physicist-notes)
12. [Exporting the PDF report](#12-exporting-the-pdf-report)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. System requirements

| Requirement | Detail |
|---|---|
| Operating system | Windows 10 (version 21H2 or later) or Windows 11 |
| Edge WebView2 runtime | Pre-installed on Windows 10 21H2+ and all Windows 11. If missing, download the Evergreen installer from [Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) |
| PRIME data | Trajectory log files and `couchShifts.txt` as exported by the PRIME system |

No Python, Node.js, or any other runtime installation is required — the exe
is fully self-contained.

---

## 2. Launching the application

Double-click **KIM-QA-Reporter.exe**. A desktop window opens — there is no
browser involved. The first launch may take a few seconds while Windows
extracts the bundled runtime to a temporary folder.

> The title bar shows the current version (e.g. `KIM-QA Reporter v0.1.0`).

---

## 3. Data folder layout

The application expects a patient directory structured as follows:

```
<PatientFolder>/
├── Centroid_<PatientID>_BeamID_*.txt   ← seed/isocenter file
├── FX01/
│   └── Trajectory Logs/
│       ├── MarkerLocationsGA_CouchShift_0.txt
│       ├── MarkerLocationsGA_CouchShift_1.txt
│       ├── MarkerLocationsGA_CouchShift_2.txt   ← one file per beam segment
│       └── couchShifts.txt
├── FX02/
│   └── Trajectory Logs/
│       └── …
└── …
```

**Centroid file location:** The `Centroid_*.txt` file can sit either inside the
patient folder or one level above it — both layouts are handled automatically.

---

## 4. Loading a patient

1. Click **Browse** to open a native folder picker and select the patient
   directory, **or** type the full path directly into the path box and press
   **Enter** (or click **Scan**).

2. The application scans the directory, locates the centroid file, and lists
   all available fractions. The first fraction with at least two trajectory
   files is selected automatically.

> **Tip:** The path box accepts any Windows path including UNC paths
> (`\\server\share\…`).

---

## 5. Selecting a fraction

The **Fraction** section (sidebar) shows a tab for each fraction folder found.
Each tab displays how many trajectory files (`f`) and couch-shift rows (`r`)
that fraction has — for example `FX02  3f / 4r`.

- Click a fraction tab to load it. The deviation plot and intervention table
  update immediately.
- Fractions with only **one trajectory file** are greyed out — there is no
  data to plot (a single file contains no useful deviation timeseries).

---

## 6. Reading the deviation plot

The main pane shows three stacked panels sharing the same time axis:

| Panel | Axis | Colour |
|---|---|---|
| Top | LR — Left/Right | Blue |
| Middle | SI — Superior/Inferior | Green |
| Bottom | AP — Anterior/Posterior | Red |

**X-axis:** Time from kV beam-on in minutes. Beam-off pauses longer than 5 s
are compressed to 3 s of display width and shown as a translucent grey band —
the x-axis labels always reflect real clock time.

**Dashed lines at ±2 mm:** The clinical tolerance band. Deviations beyond
±2 mm appear clearly above/below these lines.

**Dotted vertical rules:** Mark each intra-fraction couch correction. The label
(e.g. `Intra-fraction #1`) is shown above the top panel.

**Gold bands:** Highlight the ±20 s window around each correction — the region
used for the pre- and post-correction summary in the PDF. Edges are editable
(see [§10](#10-adjusting-highlight-bands)).

**Faint dotted trace (no-correction counterfactual):** For each
correction, the post-correction segment is re-drawn with the applied shift
mathematically removed to show where the tumour *would* have been had the
operator not intervened. Toggle this overlay on/off with the checkbox in the
**Export PDF report** panel.

**Plotly toolbar** (top-right of chart):
- **Scroll to zoom** — mouse wheel zooms the x-axis
- **Pan** — click and drag
- **Download PNG** — saves a high-resolution (2×) screenshot of the current view
- **Reset axes** — double-click anywhere on the chart

---

## 7. Managing active markers

PRIME implants up to three gold seeds. The **Active markers** section (sidebar)
shows a toggle button for each detected marker.

**Why you might toggle a marker off:** If one seed has migrated significantly
from its planning position, it inflates the apparent centroid displacement.
Excluding it lets the remaining seeds represent the tumour position accurately.

When you toggle a marker, the expected centroid is recomputed from the same
seed subset so both sides of the deviation calculation stay consistent — you
are not introducing an artificial offset.

> At least one marker must remain active.

---

## 8. Fixing the FX01 couch-row anomaly

**What is it?** For some patients, PRIME writes two treatment sessions into a
single `couchShifts.txt` (typically in FX01), producing stale leading rows
from the earlier session. Using all rows assigns incorrect shifts to the wrong
beam segments.

**How to fix it:**

1. Enable the **Trim leading rows** checkbox in the **Active markers** section.
2. The row count defaults to the number of trajectory files in that fraction
   (which is the canonical PRIME layout). This trims away the stale rows.
3. If the intervention table still looks wrong, adjust the number manually
   until the displayed shifts match the expected corrections.

The deviation plot and intervention table update immediately on each change.

---

## 9. Adding a manual intervention

Occasionally an operator-applied couch correction is not recorded in
`couchShifts.txt`. You can add it manually:

1. In the **Interventions** table, expand the **Add manual intervention**
   panel (click the `+` row at the bottom).
2. Enter the **time** in seconds from beam-on (visible from hovering the chart
   near the correction), the shift components in mm (ΔLR, ΔSI, ΔAP), and an
   optional label.
3. Click **Add**. The intervention appears in the table and a highlight band
   is created automatically.

To remove a manual entry, click the trash icon in its table row.

> Manual interventions are marked with a pin icon (📌) in the Source column.

---

## 10. Adjusting highlight bands

Each intra-fraction correction has an associated gold highlight band covering
±20 s around the intervention time. These bands define the pre- and
post-correction analysis windows in the PDF.

To adjust a band:
- Edit the **start** and **end** time fields (in real seconds) in the
  **Highlight (s)** column of the intervention table.

The chart updates live as you type.

---

## 11. Physicist notes

The **Physicist notes** text area (sidebar, above the export button) accepts
free-text commentary. Leave blank lines between paragraphs — each blank line
starts a new paragraph in the PDF.

Content is preserved within a session but is not persisted between application
restarts.

---

## 12. Exporting the PDF report

1. Once you are satisfied with the fraction view, click **Render** in the
   **Export PDF report** panel.
2. The report is generated and saved automatically as:
   ```
   <patient_folder>\KIM_Report_<PatientID>_<FractionID>_<YYYYMMDD>.pdf
   ```
3. A green confirmation shows the full saved path. If export fails, a red
   message explains the error.

**What the PDF contains:**
- Patient and fraction header (patient ID, fraction, active/detected markers)
- Summary: intra-fraction intervention count, peak deviations per axis,
  frame count, any loader warnings
- Three-panel deviation plot with all highlights and (optionally) the
  no-correction overlay
- Intervention table with ΔLR/ΔSI/ΔAP, magnitude, and pre/post 20 s mean
  deviations per axis
- Physicist notes
- Footer with app version and generation timestamp

**No-correction overlay checkbox:** When ticked the counterfactual overlay
appears in the embedded plot. Untick before rendering if you prefer a clean
trace for the record.

---

## 13. Troubleshooting

### "No Centroid_*.txt found"

The application searches for the centroid file inside the patient folder and
one level above it. Make sure the file is named `Centroid_*.txt` and is in
one of those two locations.

### Fraction tab is greyed out

A fraction needs at least **two** `MarkerLocationsGA_CouchShift_*.txt` files
before there is any useful deviation to display. A single-file fraction is
disabled.

### Intervention count looks wrong / shifts are mismatched

This is the FX01 couch-row anomaly — see [§8](#8-fixing-the-fx01-couch-row-anomaly).

### "No frames survived sentinel/glitch filtering"

All frames in the trajectory files were flagged as either:
- **Sentinel** (position magnitude > 50 mm) — pre-tracking-lock placeholders
  exported by PRIME before the first valid 3D lock
- **Glitch** (single-frame spike: >5 mm in LR or >12 mm in SI/AP from median)

This usually means the selected fraction contains only the run-up to
tracking lock with no valid tracking data. Check the raw `MarkerLocationsGA_*`
files to confirm, or try a different fraction.

### The app opens but shows a blank window

Edge WebView2 may not be installed or is outdated. Download the Evergreen
Bootstrapper from [microsoft.com/edge/webview2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)
and reinstall.

### Hovering the chart shows timestamps that don't match expected treatment time

The x-axis is in *display-space* minutes with beam-off pauses compressed.
Hover tooltips show the real clock time in minutes — if you need the exact
second, divide by 60 and reference the intervention table's **t (s)** column
which always shows real seconds.
