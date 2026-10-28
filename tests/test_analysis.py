from pathlib import Path
import json
import pytest
from src.recovery import recover_one, assert_agreement
from src.analysis import create_analyses

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "data/raw/manifest.json").read_text(encoding="utf-8"))

def test_required_pandas_analyses_and_numpy_population_index():
    bundle = recover_one(ROOT / "data/raw/country_records.csv", MANIFEST)
    result = create_analyses(bundle.canonical, 2007)
    assert len(result["asia_selected_year"]) == 33
    assert len(result["country_history"]) == 12
    assert result["population_index"].shape == (3, 7)
    assert list(result["population_index"]["country"]) == ["Philippines","Indonesia","Thailand"]
    assert result["population_index"]["1982"].tolist() == pytest.approx([100,100,100])
    assert int(bundle.canonical.query("continent == 'Asia' and year == 2007")["pop"].sum()) == 3811953827

def test_reporting_year_can_be_changed_without_editing_processing_functions():
    bundle = recover_one(ROOT / "data/raw/country_records.csv", MANIFEST)
    result = create_analyses(bundle.canonical, 1997)
    assert len(result["asia_selected_year"]) > 0
    assert set(result["asia_selected_year"]["year"]) == {1997}
