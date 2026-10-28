"""Helpers for machine-readable validation and audit reports."""
from __future__ import annotations
import pandas as pd

def write_validation(rows: list[dict], path) -> None:
    """Write validation checks using the required columns."""
    pd.DataFrame(rows, columns=["check","expected","actual","tolerance","pass"]).to_csv(path, index=False)

def write_audit(rows: list[dict], path) -> None:
    """Write processing audit records."""
    pd.DataFrame(rows, columns=["step","source_file","operation","rule","rows_before","rows_after"]).to_csv(path, index=False)
