# CICADA: Executable and Auditable Reasoning for Public Procurement

This repository contains the code, experiment entry points, paper, and dissertation sources for
an executable reasoning environment built from UK public-procurement records. The system represents
reasoning actions as typed programs, executes them over a provenance-preserving graph, and separates
runtime checks from offline oracle evaluation.

## Repository layout

| Path | Contents |
| --- | --- |
| `src/procurement_graph/` | Main Python package: ingestion, entity resolution, KG, QA, and reasoning runtime |
| `src/*.py` | Compatibility modules still used by the early ingestion and ER pipeline/tests |
| `pipelines/` | Numbered end-to-end data and benchmark stages |
| `scripts/` | Curated experiment, evaluation, training-export, PACS, WTQ, and demo entry points |
| `configs/` | Project settings and selected final training configurations |
| `tests/` | Unit and integration-style tests |
| `docs/` | Current architecture, benchmark, data, results, and training documentation |
| `paper/current/` | Current paper source, figures, case-study supplements, and compiled PDF |
| `thesis/` | Dissertation LaTeX source, figures, and compiled PDF |
| `data/` | Data inventory only; generated and large datasets are intentionally excluded |

Older paper versions, experiment caches, generated training exports, local model outputs, reference
PDFs, and LaTeX build intermediates are intentionally not included in this clean repository.

## Setup

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Run the tests from the repository root:

```bash
python -m pytest -q
```

The pipeline and experiment scripts add `src/` to their import path when run from the repository
root. For interactive use, set `PYTHONPATH=src` or install the package in your preferred development
environment.

## Data

The original working directory contains close to 1 GB of generated Parquet/JSONL artifacts. They
are not suitable for a clean source repository and are not required to read or review the code and
papers. See [`data/README.md`](data/README.md) for the expected layout and regeneration entry points.

Some experiments call hosted language models. Credentials must be supplied through environment
variables; never commit `.env` files, API keys, tokens, or cloud credentials.

## Main entry points

- Data and KG construction: `pipelines/00_fetch_reference.py` through `pipelines/41_validate_kg.py`
- Benchmark construction: `pipelines/50_build_qa_stage1.py` through `pipelines/64_qa_assemble.py`
- Current reasoning runtime: `src/procurement_graph/reasoning/`
- Teacher and evaluation runs: `scripts/run_teacher.py`, `scripts/run_compare.py`
- Paper: `paper/current/main.tex` and `paper/current/main.pdf`
- Dissertation: `thesis/main.tex` and `thesis/main.pdf`

## Repository note

No project-level licence was present in the source workspace. Add an explicit `LICENSE` before
advertising reuse permissions or accepting external contributions.
