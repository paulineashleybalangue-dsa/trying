from pathlib import Path
import json
import pandas as pd
import pytest
from src.recovery import recover_one
from src.exporter import write_canonical_formats, reload_and_verify

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/raw/manifest.json").read_text(encoding="utf-8"))

def test_canonical_exports_round_trip(tmp_path):
    pytest.importorskip("pyarrow")
    bundle = recover_one(ROOT / "data/raw/country_records.csv", MANIFEST)
    write_canonical_formats(bundle.canonical, tmp_path)
    checks = reload_and_verify(bundle.canonical, tmp_path)
    assert len(checks) == 4
    assert all(check["pass"] for check in checks)

def test_corrupted_export_values_fail_comparison(tmp_path):
    pytest.importorskip("pyarrow")
    bundle = recover_one(ROOT / "data/raw/country_records.csv", MANIFEST)
    write_canonical_formats(bundle.canonical, tmp_path)
    df = pd.read_csv(tmp_path / "canonical.csv")
    df.loc[0, "pop"] = int(df.loc[0, "pop"]) + 999
    df.to_csv(tmp_path / "canonical.csv", index=False)
    with pytest.raises(ValueError, match="round-trip"):
        reload_and_verify(bundle.canonical, tmp_path)
