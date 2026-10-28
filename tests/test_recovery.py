from pathlib import Path
import json
import pandas as pd
import pytest
from src.recovery import recover_one, ConflictingKeyError
from src.readers import FileSchemaError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/raw/manifest.json").read_text(encoding="utf-8"))

def test_exact_duplicates_are_removed_and_logged():
    bundle = recover_one(ROOT / "data/raw/country_records.csv", MANIFEST)
    assert bundle.raw_count == 1712
    assert len(bundle.quarantine) == 6
    assert len(bundle.duplicates) == 2
    assert len(bundle.canonical) == 1704

def test_conflicting_country_year_key_stops_processing():
    with pytest.raises(ConflictingKeyError):
        recover_one(ROOT / "data/raw/conflicting_key.csv", MANIFEST)

def test_reordered_rows_are_sorted_by_key():
    bundle = recover_one(ROOT / "data/raw/country_records.csv", MANIFEST)
    ordered = bundle.canonical.sort_values(["country","year"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(bundle.canonical, ordered)
