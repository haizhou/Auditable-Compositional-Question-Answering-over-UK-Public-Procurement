# Current paper

- `main.tex`: paper source
- `main.pdf`: compiled paper
- `figs/`: self-contained figure assets used by `main.tex`
- `*_failure_case.tex` and matching PDFs/prompt bundles: case-study supplements
- `CLAIM_EVIDENCE_LEDGER.md`: claim-to-evidence audit

Build from this directory with a standard LaTeX installation:

```bash
latexmk -pdf main.tex
```

Generated LaTeX intermediates are ignored by the repository-level `.gitignore`.
