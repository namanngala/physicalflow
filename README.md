# PhysicalFlow

**An autonomous vehicle sensor data pipeline and Data Readiness Scoring (DRS) engine for world model training.**

PhysicalFlow ingests real-world multi-modal sensor data (camera, LiDAR, RADAR) from Motional's nuScenes dataset, validates it, and produces an original composite score evaluating whether each driving scene is suitable training data for physical AI world models.

---

## Why this exists

Physical AI companies — autonomous vehicle fleets, humanoid robotics teams, drone systems — generate enormous volumes of sensor data daily. Before any world model can train on it, that data must be clean, complete, synchronized, and well-annotated. No standard automated framework exists to score this readiness. PhysicalFlow is one.

Bad training data in physical AI isn't just an accuracy problem — it's a safety problem. A model trained on corrupt sensor data learns wrong physics. PhysicalFlow catches issues like dropped frames, unsynchronized sensors, and unconfirmed ("ghost") annotations before they reach a model.

---

## What it does

1. **Ingests** raw nuScenes sensor data (6 cameras, 1 LiDAR, 5 RADAR, GPS, IMU) via the official nuscenes-devkit
2. **Parses** the relational token-based schema into clean, flat records
3. **Loads** data into a DuckDB time-series database, idempotently
4. **Validates** frame completeness, sensor timestamp alignment, and annotation confirmation
5. **Scores** every scene across 5 dimensions into a single Data Readiness Score (0-100)
6. **Visualizes** results in an interactive Streamlit dashboard

---

## The Data Readiness Score (DRS)

A weighted composite of 5 independently auditable dimensions:

| Dimension | Weight | What It Measures |
|---|---|---|
| D1 — Sensor Coverage | 25% | Fraction of expected 12 sensor channels present per scene |
| D2 — Frame Completeness | 25% | Actual vs expected sample count, capped at 100 |
| D3 — Timestamp Alignment | 20% | Camera-LiDAR sync delta, calibrated against observed data |
| D4 — Annotation Validity | 20% | Valid annotation ratio, penalized by ghost annotation rate |
| D5 — Scene Diversity | 10% | Distinct object categories present vs 23 possible classes |

```
DRS = 0.25(D1) + 0.25(D2) + 0.20(D3) + 0.20(D4) + 0.10(D5)
```

Every sub-score traces directly to raw nuScenes schema fields — fully auditable, no black boxes. Full methodology and research grounding in [`docs/methodology.md`](docs/methodology.md).

### Engineering note on D3

The original design measured timestamp sync across all 12 sensors. Real measured deltas (40-83ms) revealed this was dominated by RADAR units with independent firing schedules — not camera-LiDAR fusion-critical sync. D3 was redesigned to measure only the camera-LiDAR pair, the actual fusion-critical relationship in AV perception, with its threshold recalibrated against observed data rather than a theoretical estimate. This is documented as a known simplification: raw camera-LiDAR delta is a proxy that partially reflects LiDAR rotation timing behavior, not pure sync error (see methodology doc).

---

## Results on nuScenes v1.0-mini

Across all 10 scenes, DRS scores ranged from 70.1 to 76.1 (average 72.8) — scores clustered tightly, suggesting the mini dataset is consistent in quality with no scenes that are unambiguously excellent or poor for training. Sensor coverage and frame completeness were perfect (100.0) across every scene; annotation validity and scene diversity were the primary differentiators between higher and lower scoring scenes.

---

## Tech stack

- **Python** — pipeline logic, OOP, file I/O
- **DuckDB** — embedded OLAP database for time-series sensor queries
- **nuscenes-devkit** — official dataset access library
- **Streamlit + Plotly** — interactive dashboard
- **Git/GitHub** — version control

No cloud services, no paid tools, runs entirely on a local machine.

---

## Project structure

```
physicalflow/
├── data/
│   ├── raw/              # nuScenes source files (untouched)
│   └── processed/        # DuckDB database
├── src/
│   ├── ingestion/         # loader.py, parser.py
│   ├── database/          # schema.py, loader.py
│   ├── validation/        # quality.py
│   ├── scoring/           # drs.py
│   └── dashboard/         # app.py
├── main.py                 # runs the full pipeline
├── config.py                # paths, thresholds, single source of truth
└── requirements.txt
```

---

## Running it

```bash
git clone https://github.com/namanngala/physicalflow.git
cd physicalflow
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```

Download [nuScenes v1.0-mini](https://www.nuscenes.org/download) (free account required) and place its contents in `data/raw/`.

```bash
python main.py                              # run the pipeline
streamlit run src/dashboard/app.py          # view the dashboard
```

---

## Data source

Built on the [nuScenes dataset](https://www.nuscenes.org/) by Motional, used under their non-commercial research license. nuScenes provides synchronized data from a full autonomous vehicle sensor suite across 1,000 real-world driving scenes in Boston and Singapore.

---

## Author

Built independently by [Naman](https://github.com/namanngala) as a hands-on transition project from data engineering into physical AI / autonomous systems data infrastructure.
