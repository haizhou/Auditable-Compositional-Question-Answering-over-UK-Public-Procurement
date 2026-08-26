# Data layout

Large, generated, and potentially redistributable data artifacts are deliberately excluded from
this repository. Do not commit the full working `data/` directory directly.

The code expects the following layout when running the complete pipeline:

```text
data/
  raw/          downloaded OCDS releases
  interim/      flattened intermediate tables
  reference/    official organisation reference data
  entities/     entity-resolution tables
  extracted/    extracted contract/evidence tables
  kg/           graph node and edge Parquet files
  qa/           generated benchmarks, traces, and evaluation outputs
  training/     generated training exports
```

Start with `configs/settings.yaml`. The numbered scripts in `pipelines/` build reference data,
ingest source releases, resolve entities, extract records, construct the graph, and generate the QA
benchmark. Training exports and evaluation artifacts are produced by the curated scripts under
`scripts/`.

If public data artifacts are released later, publish them as a versioned GitHub Release, an
institutional archive, or a dataset repository and record checksums and download instructions here.
Git LFS should only be used when the repository genuinely needs a small number of versioned binary
artifacts.
