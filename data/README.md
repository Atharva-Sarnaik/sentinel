# data/

This directory is **gitignored** and **DVC-tracked**.

## Fetching datasets

After cloning, run:

```bash
# Install DVC
pip install dvc

# Pull all tracked data (requires DVC remote access)
dvc pull
```

## Dataset directory structure (after pull)

```
data/
├── raw/
│   ├── SMAP/          # NASA SMAP anomaly dataset
│   ├── MSL/           # NASA MSL anomaly dataset
│   ├── ESA-ADB/       # ESA Anomaly Detection Benchmark (fallback)
│   └── OPS-SAT/       # ESA OPS-SAT operational telemetry (fallback)
├── processed/         # Windowed, normalised feature store (Parquet + DuckDB)
└── splits/            # Chronological train/test index files
```

## Dataset acquisition

| Dataset | Source | Notes |
|---|---|---|
| SMAP | [NASA PO.DAAC](https://podaac.jpl.nasa.gov/) | Public download |
| MSL | [NASA PO.DAAC](https://podaac.jpl.nasa.gov/) | Public download |
| ESA-ADB | [ESA Open Data](https://www.esa.int/) | Fallback if SMAP/MSL T0.5 spike fails |
| OPS-SAT | [ESA](https://www.esa.int/Enabling_Support/Operations/OPS-SAT) | Fallback |

> **Risk R1:** The SMAP/MSL channel-to-subsystem grouping is unverified until task T0.5 completes. See ADR-0001.

## Never commit data files

Raw and processed data must never be committed to git. Only `.dvc` pointer files are tracked. The `.gitignore` excludes all data extensions.

