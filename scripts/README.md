# Scripts

Shell scripts to run Drain, UniParser, the hybrid pipeline, and result analysis. All paths in the table below are relative to the **repository root** unless noted.

**Prerequisites**

- **Drain / evaluation**: Python venv at `benchmark/logparser/Drain/.venv` and `benchmark/evaluation/.venv` (or adjust scripts).
- **UniParser**: Conda env named `UniParser` (see `benchmark/logparser/UniParser/README.md`).
- **Analyzer**: Python venv at `benchmark/analyzer/venv`.

**Dataset sizes**

- **2k**: Small dataset under `2k_dataset/` (quick runs).
- **full**: Full Loghub benchmark (long runs, large disk usage).

---

## Quick reference

| Script | What it does |
|--------|----------------|
| [clean_results.sh](clean_results.sh) | Deletes `result/` and recreates it (fresh start). |
| **Drain** | |
| [Drain/2k/drain_parse_only_2k.sh](Drain/2k/drain_parse_only_2k.sh) | Run Drain on 2k dataset (parsing only). |
| [Drain/2k/drain_eval_only_2k.sh](Drain/2k/drain_eval_only_2k.sh) | Evaluate Drain results on 2k (after parse). |
| [Drain/full/drain_parse_only_full.sh](Drain/full/drain_parse_only_full.sh) | Run Drain on full dataset; logs to `result/drain_run_*.log`. |
| [Drain/full/drain_eval_only_full.sh](Drain/full/drain_eval_only_full.sh) | Evaluate Drain results on full dataset. |
| **UniParser** | |
| [UniParser/2k/uniparser_preprocess_only_2k.sh](UniParser/2k/uniparser_preprocess_only_2k.sh) | Convert 2k logs to NER format (step 1). |
| [UniParser/2k/uniparser_train_only_2k.sh](UniParser/2k/uniparser_train_only_2k.sh) | Train UniParser on 2k (step 2). |
| [UniParser/2k/uniparser_parser_only_2k.sh](UniParser/2k/uniparser_parser_only_2k.sh) | Run UniParser inference on 2k (step 3). |
| [UniParser/full/...](UniParser/full/) | Same three steps for the full dataset (`-full`). |
| **Hybrid (Drain + UniParser)** | |
| [Hybrid/2k/clean_and_run_everything.sh](Hybrid/2k/clean_and_run_everything.sh) | Full 2k pipeline: Drain → UniParser → merge → evaluate. |
| [Hybrid/2k/merge_results.sh](Hybrid/2k/merge_results.sh) | Merge Drain and UniParser outputs for 2k only. |
| [Hybrid/2k/evaluation_only.sh](Hybrid/2k/evaluation_only.sh) | Run hybrid evaluation on 2k (after merge). |
| [Hybrid/full/clean_and_run_everything.sh](Hybrid/full/clean_and_run_everything.sh) | Same as 2k but for full dataset (uses `-full` where applicable). |
| [Hybrid/full/merge_results.sh](Hybrid/full/merge_results.sh) | Merge results for full dataset. |
| [Hybrid/full/evaluation_only.sh](Hybrid/full/evaluation_only.sh) | Hybrid evaluation on full dataset. |
| **Analyzer** | |
| [Analyzer/2k/analyze_results.sh](Analyzer/2k/analyze_results.sh) | Run analyzer on 2k results (`benchmark/analyzer/analyzer_2k.py`). |
| [Analyzer/full/analyze_results.sh](Analyzer/full/analyze_results.sh) | Run analyzer on full results (`analyzer_full.py`). |

---

## What each script does

### clean_results.sh

- Removes the `result/` directory and creates an empty one.
- Use when you want to re-run the pipeline from scratch (parsing + evaluation).

**Run from:** repository root  
`./scripts/clean_results.sh`

---

### Drain

Drain is the rule-based log parser (fixed-depth tree). These scripts run it and then evaluate metrics (e.g. GA, PA, FTA).

- **drain_parse_only_2k.sh**  
  - `cd` → `benchmark/logparser/Drain`, activates `.venv`, runs `run_drain.py -otc` (2k, with oracle template correction).  
  - Writes under `result/result_Drain_2k/`.

- **drain_eval_only_2k.sh**  
  - `cd` → `benchmark/evaluation`, runs `evaluator.py -otc -drain` to compute metrics for Drain 2k results.

- **drain_parse_only_full.sh**  
  - Same as parse-only but for full dataset: `run_drain.py -full`, with stdout/stderr teed to `result/drain_run_<timestamp>.log`.

- **drain_eval_only_full.sh**  
  - Evaluation for Drain full: `evaluator.py -full -drain`.

**Run from:** repository root, e.g.  
`./scripts/Drain/2k/drain_parse_only_2k.sh`  
`./scripts/Drain/2k/drain_eval_only_2k.sh`

---

### UniParser

UniParser is the LSTM-based parser. It has three stages: preprocess → train → infer. Scripts are split so you can run each stage separately.

1. **Preprocess**  
   Converts logs to NER-style input.  
   - 2k: `process_log_parsing_input_to_ner.py` (no args).  
   - full: same script with `-full`.

2. **Train**  
   Trains the NER model.  
   - 2k: `TrainNERLogAll.py`.  
   - full: `TrainNERLogAll.py -full`.

3. **Parse**  
   Runs inference to produce templates.  
   - 2k: `InferNERLogAll.py`.  
   - full: `InferNERLogAll.py -full`.

All UniParser scripts use the `UniParser` conda env and set `CUDA_VISIBLE_DEVICES=1` (change in the script if needed).

**Run from:** repository root, in order:  
`./scripts/UniParser/2k/uniparser_preprocess_only_2k.sh`  
`./scripts/UniParser/2k/uniparser_train_only_2k.sh`  
`./scripts/UniParser/2k/uniparser_parser_only_2k.sh`

---

### Hybrid (Drain + UniParser)

The hybrid pipeline runs both parsers, merges their outputs, then runs the hybrid evaluator.

**Order of operations**

1. Run **Drain** (parse) → `result/result_Drain_2k/` or `result_Drain_full/`.
2. Run **UniParser** (preprocess → train → parse) → `result/result_UniParser_2k/` or `result_UniParser_full/`.
3. **Merge** Drain and UniParser results → merged outputs used by the evaluator.
4. **Evaluate** with `evaluator.py -hybrid` (and `-otc` for 2k, `-full` for full).

**All-in-one**

- **Hybrid/2k/clean_and_run_everything.sh**  
  Runs: Drain (2k) → UniParser inference only (2k) → merge (2k) → hybrid evaluation (2k).  
  Preprocess and train are commented out (assumes they were run once).  
  Logs to `~/tesina/DrainUP/logs/` (script uses absolute paths; edit if your repo is elsewhere).

- **Hybrid/full/clean_and_run_everything.sh**  
  Same idea for the full dataset (Drain full, UniParser inference full, merge full, eval full).

**Step-by-step (2k)**

1. Drain: `./scripts/Drain/2k/drain_parse_only_2k.sh`
2. UniParser: run the three UniParser/2k scripts in order (preprocess, train, parser).
3. Merge: `./scripts/Hybrid/2k/merge_results.sh`
4. Eval: `./scripts/Hybrid/2k/evaluation_only.sh`

For **full**, use the full Drain scripts, full UniParser scripts, then `Hybrid/full/merge_results.sh` and `Hybrid/full/evaluation_only.sh`.

---

### Analyzer

Post-hoc analysis of parsing/evaluation results (e.g. summaries, comparisons).

- **Analyzer/2k/analyze_results.sh**  
  - `cd` → `benchmark/analyzer`, activates `venv`, runs `analyzer_2k.py`.

- **Analyzer/full/analyze_results.sh**  
  - Same but runs `analyzer_full.py`.

**Run from:** repository root  
`./scripts/Analyzer/2k/analyze_results.sh` or `./scripts/Analyzer/full/analyze_results.sh`

---

## Running everything together (2k, step-by-step)

```bash
# Optional: start clean
./scripts/clean_results.sh

# 1. Drain
./scripts/Drain/2k/drain_parse_only_2k.sh
./scripts/Drain/2k/drain_eval_only_2k.sh

# 2. UniParser (in order)
./scripts/UniParser/2k/uniparser_preprocess_only_2k.sh
./scripts/UniParser/2k/uniparser_train_only_2k.sh
./scripts/UniParser/2k/uniparser_parser_only_2k.sh

# 3. Hybrid merge + evaluation
./scripts/Hybrid/2k/merge_results.sh
./scripts/Hybrid/2k/evaluation_only.sh

# 4. Analyze
./scripts/Analyzer/2k/analyze_results.sh
```

Or use the all-in-one 2k script (after editing paths if needed):

```bash
./scripts/Hybrid/2k/clean_and_run_everything.sh
```

(UniParser preprocess and train are skipped there; run them at least once beforehand if you need to (re)train.)
