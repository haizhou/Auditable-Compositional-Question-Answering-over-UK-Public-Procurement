# Script groups

- Root scripts: current benchmark construction, evaluation, training export, analysis, and demos.
- `pacs/`: PACS construction and evaluation utilities.
- `wtq/`: selected WikiTableQuestions portability utilities.
- `paper_figures/`: scripts needed by the current paper and its cited analyses.

Historical one-off runs and superseded version chains from the working directory were intentionally
left out. The authoritative reusable implementation lives under `src/procurement_graph/`; scripts
are command-line entry points around that package.
