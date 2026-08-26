"""Backward-compatible imports for the original flat ingestion module.

The maintained implementation lives in :mod:`procurement_graph.ingest.loader`.
"""

from procurement_graph.ingest.loader import (
    extract_release_row,
    flatten_all_years,
    load_interim,
    load_year,
    write_interim,
)

__all__ = [
    "extract_release_row",
    "flatten_all_years",
    "load_interim",
    "load_year",
    "write_interim",
]
