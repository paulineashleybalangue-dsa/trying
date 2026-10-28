"""Recovery orchestration, duplicate removal, conflicts, and agreement checks."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np
from .readers import read_records, FileSchemaError
from .validator import validate_records, CANONICAL

class ConflictingKeyError(ValueError):
    """Raised when a country-year key has multiple valid payloads."""

@dataclass
class RecoveryBundle:
    """Results from recovering one source format."""
    source_file: str
    raw_count: int
    canonical: pd.DataFrame
    quarantine: pd.DataFrame
    duplicates: pd.DataFrame
    audit: list[dict]

def recover_one(path: Path, manifest: dict) -> RecoveryBundle:
    """Parse, validate, quarantine, deduplicate and sort one source file."""
    raw = read_records(path, manifest)
    result = validate_records(raw, path.name, manifest["allowed_years"], manifest["allowed_continents"])
    valid = result.valid.copy()
    key = manifest.get("key", ["country", "year"])
    duplicate_mask = valid.duplicated(subset=CANONICAL, keep="first")
    duplicates = valid.loc[duplicate_mask].copy()
    deduped = valid.loc[~duplicate_mask].copy()
    if deduped.duplicated(subset=key, keep=False).any():
        conflicted = deduped[deduped.duplicated(subset=key, keep=False)].sort_values(key)
        raise ConflictingKeyError(
            f"Conflicting key(s) in {path.name}: {conflicted[key].to_dict('records')}"
        )
    deduped = deduped.sort_values(["country", "year"], kind="stable").reset_index(drop=True)
    audit = [
        {"step":1,"source_file":path.name,"operation":"parse_and_normalize","rule":"manifest layout and canonical schema","rows_before":len(raw),"rows_after":len(raw)},
        {"step":2,"source_file":path.name,"operation":"validate","rule":"manifest value/domain rules","rows_before":len(raw),"rows_after":len(result.valid)},
        {"step":3,"source_file":path.name,"operation":"quarantine_invalid","rule":"retain original fields and source record number","rows_before":len(raw),"rows_after":len(result.valid)},
        {"step":4,"source_file":path.name,"operation":"remove_exact_duplicates","rule":"all six canonical fields identical","rows_before":len(valid),"rows_after":len(deduped)},
        {"step":5,"source_file":path.name,"operation":"sort","rule":"country then year","rows_before":len(deduped),"rows_after":len(deduped)},
    ]
    dup_log = duplicates.copy()
    if not dup_log.empty:
        dup_log.insert(0, "source_file", path.name)
        dup_log.insert(1, "source_record", "duplicate_copy")
        dup_log.insert(2, "reason", "exact_duplicate_valid_record")
    else:
        dup_log = pd.DataFrame(columns=["source_file","source_record","reason",*CANONICAL])
    return RecoveryBundle(path.name, len(raw), deduped, result.quarantine, dup_log, audit)

def assert_agreement(bundles: list[RecoveryBundle], atol: float = 1e-8) -> pd.DataFrame:
    """Compare four recovered datasets by key and canonical values."""
    if not bundles:
        raise ValueError("No input datasets supplied")
    base = bundles[0].canonical.reset_index(drop=True)
    for bundle in bundles[1:]:
        other = bundle.canonical.reset_index(drop=True)
        if len(base) != len(other):
            raise ValueError(f"Row-count disagreement: {bundles[0].source_file} vs {bundle.source_file}")
        for col in ["country","continent","year","pop"]:
            if not base[col].equals(other[col]):
                raise ValueError(f"Exact agreement failed for {col}: {bundle.source_file}")
        for col in ["lifeExp","gdpPercap"]:
            if not np.allclose(base[col].to_numpy(float), other[col].to_numpy(float),
                               atol=atol, rtol=0, equal_nan=True):
                raise ValueError(f"Numeric agreement failed for {col}: {bundle.source_file}")
    return base.copy()
