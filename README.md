# DrainUP — Combining Semantic and Statistical Techniques for Robust Template Extraction and Parsing

Thesis: A hybrid log parsing pipeline that combines **Drain** (rule-based, fast) with **UniParser** (LSTM-based, semantic) for robust log template extraction, evaluated on the Loghub benchmark.

---

## Context and motivation

Existing log parsing solutions trade off between two incompatible strengths: semantic (local) parsers, which achieve high accuracy at extracting fine-grained event structure from individual log lines, and statistical (global) parsers, which group logs consistently across a corpus using pattern statistics. No single approach reliably provides both precise local parsing and coherent global grouping. As a result, practitioners must choose between per-log correctness and global consistency—a trade-off that reduces parser utility in real SRE environments where logs come from diverse frameworks, heterogeneous systems, and rapidly evolving formats. The core deficiency is the lack of a unified method that integrates semantic understanding for local accuracy with statistical patterning for global consistency, leaving many parsers context-dependent and unable to generalize across systems and logging practices.

---

## Research Questions

### 1. RQ1 — Accuracy trade-off:

Question: Does a hybrid parser that combines semantic (e.g. LSTM-based, learning-based) and statistical methods achieve superior parsing accuracy compared to standalone semantic and standalone statistical baselines across diverse log formats?

Why it matters (motivation): semantic parsers excel at per-line field extraction while statistical parsers excel at corpus-level template consistency. Demonstrating that a hybrid approach outperforms both baselines establishes the core claim of the thesis.

Hypothesis: A hybrid semantic+statistical parser will achieve higher per-line extraction and better template grouping scores than either semantic-only or statistical-only parsers on average across heterogeneous datasets.

### 2. RQ2 — Workload distribution, cost & latency:

Question: How does the distribution of parsing workload between semantic and statistical components affect the trade-off between parsing accuracy, computational cost, and processing latency?

Why it matters (motivation): real deployments care about cost and latency — learning-based semantic parsing (e.g. LSTM) is often more costly/slow than statistical methods. A hybrid must allow controllable trade-offs.

Hypothesis: Carefully allocating high-value/ambiguous lines to the semantic component while routing routine lines to the statistical component yields near-semantic accuracy at significantly lower cost and latency than a semantic-only pipeline. There exists a Pareto frontier of accuracy vs cost/latency obtainable by tuning this allocation.


### 3. RQ3 — Cross-system generalization & adaptation:

Question: To what extent does the hybrid approach improve generalization across different logging frameworks and system types without requiring retraining or heavy reconfiguration?

Why it matters (motivation): SRE environments are heterogeneous; a practical parser must generalize zero-shot or with minimal adaptation.

Hypothesis: The hybrid approach provides stronger zero-shot generalization than statistical-only parsers and requires fewer labeled examples (or smaller adaptation steps) to reach in-domain performance than semantic-only parsers when confronted with novel logging frameworks.

---

## Investigation Objectives

I have 3 main objectives for this thesis:

The first is to design and implement a hybrid log parsing architecture that effectively combines semantic-based parsers for local token-level analysis with statistical-based parsers for global pattern recognition and grouping. This objective involves producing a modular, end-to-end pipeline with a semantic component and a statistical component. The architecture will include a routing or selector mechanism that decides, based on confidence or rarity, which lines are escalated to the semantic module and which are handled by the statistical module.

The second one is to conduct a comprehensive evaluation comparing the hybrid parser's accuracy and computational efficiency against state-of-the-art semantic-based and statistical-based baseline parsers using publicly available benchmark datasets, in this specific case, LogHub 2.0. The evaluation will use the metrics provided by the LogHub benchmark to compare my solution to the state-of-the-art parsers (Drain and UniParser).

And as the third one, I am going to assess the generalization capabilities of the hybrid approach across multiple logging frameworks, system types, and log format variations to validate its applicability in diverse SRE production environments. The analysis will compare how the hybrid approach’s combination of semantic understanding and statistical grounding affects sample efficiency and robustness relative to purely semantic or purely statistical baselines, and will surface concrete deployment guidance.

---

## Approach

The project uses **Drain** (fixed-depth tree, similarity threshold) for efficient template extraction and adds confidence-related logic to identify uncertain parses. **UniParser** (LSTM-based NER) provides a semantic, learning-based alternative. The **hybrid** pipeline runs both parsers and merges their outputs; the evaluation harness computes grouping accuracy (GA), parsing accuracy (PA), and template-level metrics (FGA, PTA, RTA, FTA). Results can be analyzed and visualized with the provided analyzer (comparison tables and plots).

---

## Repository structure

| Path | Description |
|------|-------------|
| `benchmark/` | Parsers (Drain, UniParser), evaluation harness, and analyzer. |
| `benchmark/logparser/Drain/` | Drain implementation (with confidence-related extensions). |
| `benchmark/logparser/UniParser/` | UniParser (LSTM) implementation. |
| `benchmark/evaluation/` | Evaluation scripts (metrics, merge, hybrid evaluation). |
| `benchmark/analyzer/` | Post-hoc analysis and comparison plots (Drain vs UniParser vs DrainUP). |
| `2k_dataset/` | Loghub 2k datasets and per-dataset citation READMEs. |
| `scripts/` | Shell scripts to run parsing, evaluation, merge, and analysis (2k and full). |
| `SETUP.md` | Installation and environment setup (venvs, Conda). |
| `scripts/README.md` | Detailed description of each script and how to run the pipeline. |
| `NOTICE` | Third-party attribution (LOGPAI, University of Luxembourg, Loghub). |
| `LICENSE` | Project license (see also `2k_dataset/LICENSE.txt` for dataset terms). |

---

## Getting started

1. **Setup** — Install dependencies and create environments (Drain and evaluation venvs, UniParser Conda env, analyzer venv). See **[SETUP.md](SETUP.md)**.
2. **Run the pipeline** — Use the scripts under `scripts/` in the order described in **[scripts/README.md](scripts/README.md)** (e.g. Drain → UniParser → merge → evaluate → optional analyzer). For a quick run on the 2k dataset:
   ```bash
   ./scripts/clean_results.sh
   ./scripts/Drain/2k/drain_parse_only_2k.sh
   ./scripts/Drain/2k/drain_eval_only_2k.sh
   # … then UniParser steps, merge, evaluation, analyzer as in scripts/README.md
   ```

---

## Documentation

- **[SETUP.md](SETUP.md)** — Python version, venvs, Conda, and requirements for each component.
- **[scripts/README.md](scripts/README.md)** — What each script does and how to run the full pipeline (2k and full).
- **[benchmark/analyzer/README.md](benchmark/analyzer/README.md)** — What the analyzer does and what result files it expects.
- **Dataset and parsers** — Citation and attribution: `2k_dataset/README.md`, `benchmark/logparser/Drain/README.md`, `benchmark/logparser/UniParser/README.md`.

---

## Attribution and license

This project builds on **LOGPAI/Loghub** (Drain, benchmark, datasets), **UniParser**, and **University of Luxembourg** (TA-Eval-Rep evaluation utilities). See **[NOTICE](NOTICE)** for full attribution and **[LICENSE](LICENSE)** for the project license. Dataset terms: **2k_dataset/LICENSE.txt**.

**Thesis:** Ingeniería en Computación Inteligente, Universidad Autónoma de Aguascalientes, 2026.  
**Author:** Diego Emilio Moreno Sanchez.
