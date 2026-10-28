from pathlib import Path
import json
import pytest
from src.readers import read_records, FileSchemaError, CANONICAL

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/raw/manifest.json").read_text(encoding="utf-8"))

@pytest.mark.parametrize("filename", ["country_records.csv", "country_records.xlsx", "country_records.json", "country_records.parquet"])
def test_readers_normalize_to_canonical_columns(filename):
    if filename.endswith(".parquet"):
        pytest.importorskip("pyarrow")
    df = read_records(ROOT / "data/raw" / filename, MANIFEST)
    assert list(df.columns) == CANONICAL
    assert len(df) == 1712

def test_missing_column_is_file_level_error():
    with pytest.raises(FileSchemaError, match="Missing|required"):
        read_records(ROOT / "data/raw/missing_column.csv", MANIFEST)

def test_unsupported_existing_format_is_rejected():
    with pytest.raises(FileSchemaError, match="Unsupported"):
        read_records(ROOT / "data/raw/unsupported.txt", MANIFEST)
