# Setup

How to install dependencies and prepare environments for running Drain, UniParser, the evaluation pipeline, and the analyzer. All paths below are relative to the **repository root**.

## Python version

- **Drain and evaluation:** Python **3.11** is recommended (used in development).
- **UniParser:** Python **3.8** is required by its dependencies (see `benchmark/logparser/UniParser/README.md`). Use a separate Conda environment.
- **Analyzer:** Python 3.8+ with pandas/matplotlib/seaborn; using the same interpreter as the evaluation env is fine.

## 1. Drain (parser)

- **Directory:** `benchmark/logparser/Drain/`
- **Environment:** Python venv (e.g. `.venv` in that directory).
- **Requirements:** `benchmark/logparser/Drain/requirements.txt`

```bash
cd benchmark/logparser/Drain
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

Scripts expect the venv to be at `benchmark/logparser/Drain/.venv` (see `scripts/Drain/`).

## 2. Evaluation (benchmark harness)

- **Directory:** `benchmark/evaluation/`
- **Environment:** Python venv (e.g. `.venv` in that directory).
- **Requirements:** `benchmark/evaluation/requirements.txt`

```bash
cd benchmark/evaluation
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

Scripts expect `benchmark/evaluation/.venv`. The same dependency set as Drain is often sufficient; you can reuse one venv for both if you prefer (create it in one place and point both script families at it, or create two for isolation).

## 3. UniParser (LSTM parser)

- **Directory:** `benchmark/logparser/UniParser/`
- **Environment:** **Conda** env named `UniParser` (Python 3.8).
- **Requirements:** `benchmark/logparser/UniParser/requirements.txt`

UniParser uses PyTorch and other packages that are best installed with Conda. From the repo root:

```bash
conda create -n UniParser python=3.8 -y
conda activate UniParser
cd benchmark/logparser/UniParser
pip install -r requirements.txt
```

If `pip install -r requirements.txt` fails, install key packages manually (e.g. `torch`, `spacy`, `gensim`) as in the project notes. The scripts under `scripts/UniParser/` call `conda activate UniParser` and assume this env exists.

## 4. Analyzer (plots and comparison)

- **Directory:** `benchmark/analyzer/`
- **Environment:** Python venv named `venv` in that directory.
- **Requirements:** `benchmark/analyzer/requirements.txt`

```bash
cd benchmark/analyzer
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
deactivate
```

Scripts expect `benchmark/analyzer/venv`. See `benchmark/analyzer/README.md` for what the analyzer does and what result files it needs.

## Quick checklist

| Component   | Location                        | Env type | Env name/path              |
|------------|----------------------------------|----------|----------------------------|
| Drain      | `benchmark/logparser/Drain/`     | venv     | `.venv`                    |
| Evaluation | `benchmark/evaluation/`           | venv     | `.venv`                    |
| UniParser  | `benchmark/logparser/UniParser/` | Conda    | `UniParser` (Python 3.8)   |
| Analyzer   | `benchmark/analyzer/`            | venv     | `venv`                     |

## After setup

- Run the pipeline using the scripts under `scripts/`; see **`scripts/README.md`** for the order of steps (Drain → UniParser → merge → evaluate → analyze) and which script to run for 2k vs full dataset.
- Optional: run `scripts/clean_results.sh` to clear `result/` before a full re-run.
