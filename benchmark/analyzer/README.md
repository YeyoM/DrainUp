# Analyzer

Post-hoc analysis and comparison of log parser results: **Drain**, **UniParser**, and **DrainUP** (hybrid). Reads evaluation summary CSVs and optional parsing-time files, then prints statistics and generates plots.

## Contents

| File | Purpose |
|------|--------|
| `analyzer_2k.py` | Run analysis on **2k** dataset results. Plots go to `plots/`. |
| `analyzer_full.py` | Same analysis for **full** dataset results. Plots go to `plots_full/`. |
| `requirements.txt` | Python deps: pandas, numpy, matplotlib, seaborn. |
| `analysis_results.csv` | Example output (combined metrics per parser × dataset). |

## Prerequisites

- Python venv with dependencies installed, e.g.:
  ```bash
  python -m venv venv
  source venv/bin/activate   # or: venv\Scripts\activate on Windows
  pip install -r requirements.txt
  ```

- **Input files** must exist under `../../result/` (relative to this directory, i.e. the repo `result/` folder). The scripts expect:

  **For 2k (`analyzer_2k.py`):**
  - `result/Drain_2k_complex=0_frequent=0.csv`
  - `result/UniParser_2k_complex=0_frequent=0.csv`
  - `result/DrainUP_2k_complex=0_frequent=0.csv`
  - Optional: `result/result_Drain_2k/parsing_times.json`, `result/result_UniParser_2k/infer_time_2k.txt`, `result/result_DrainUP_2k/parsing_times.json`

  **For full (`analyzer_full.py`):**
  - Same pattern with `_full` and `full` in paths (e.g. `Drain_full_complex=0_frequent=0.csv`).

  These CSVs are produced by the evaluation step (e.g. `evaluator.py -otc -drain`, `-hybrid`, etc.). If a file is missing, the script will fail when loading it; you can edit the `csv_files` and `time_files` dicts in `main()` to match your layout or omit parsers you did not run.

## What the analysis does

1. **Load data** – Reads the summary CSVs (one per parser) and optionally parsing-time files (JSON for Drain/DrainUP, TXT for UniParser).
2. **Combine** – Builds a single dataframe with one row per (parser, dataset) and columns for metrics (GA, PA, FGA, PTA, RTA, FTA, parse_time).
3. **Summaries** – Prints overall means/stds per parser, metric winners (best average), and parser rankings.
4. **Plots** – Generates:
   - Bar chart of average metrics across datasets
   - Heatmaps of each metric per dataset × parser
   - Speed vs accuracy scatter (GA, PA, FGA vs parse_time)
   - Radar chart of average scores
   - “Winners per dataset” horizontal bar charts
5. **Export** – Writes the combined table to `analysis_results.csv` in this directory.

## How to run

**From repo root (recommended):**

```bash
./scripts/Analyzer/2k/analyze_results.sh   # 2k
./scripts/Analyzer/full/analyze_results.sh # full
```

Those scripts `cd` to `benchmark/analyzer`, activate `venv`, and run the corresponding Python file.

**From this directory:**

```bash
source venv/bin/activate
python analyzer_2k.py   # or analyzer_full.py
```

Run after you have completed the Drain, UniParser, and (for DrainUP) hybrid merge + evaluation steps so that the expected CSVs and time files exist under `result/`.
