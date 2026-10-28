"""Safe export staging and round-trip verification."""
from __future__ import annotations
import json, shutil
from pathlib import Path
import pandas as pd
import numpy as np
from .validator import CANONICAL

def write_canonical_formats(canonical: pd.DataFrame, folder: Path) -> None:
    """Write all four canonical formats into a staging folder."""
    folder.mkdir(parents=True, exist_ok=True)
    canonical[CANONICAL].to_csv(folder / "canonical.csv", index=False)
    with pd.ExcelWriter(folder / "canonical.xlsx", engine="openpyxl") as writer:
        canonical[CANONICAL].to_excel(writer, sheet_name="observations", index=False)
    canonical[CANONICAL].to_json(folder / "canonical.json", orient="records", indent=2)
    canonical[CANONICAL].to_parquet(folder / "canonical.parquet", index=False, engine="pyarrow")

def reload_and_verify(canonical: pd.DataFrame, folder: Path, atol: float = 1e-8) -> list[dict]:
    """Reload every export, normalize types, and compare with the in-memory table."""
    checks = []
    readers = {
        "csv": lambda p: pd.read_csv(p),
        "xlsx": lambda p: pd.read_excel(p, sheet_name="observations"),
        "json": lambda p: pd.read_json(p, orient="records"),
        "parquet": lambda p: pd.read_parquet(p)
    }
    for suffix, reader in readers.items():
        path = folder / f"canonical.{suffix}"
        loaded = reader(path)[CANONICAL]
        loaded["country"] = loaded["country"].astype(str)
        loaded["continent"] = loaded["continent"].astype(str)
        loaded["year"] = pd.to_numeric(loaded["year"], errors="raise").astype("int64")
        loaded["pop"] = pd.to_numeric(loaded["pop"], errors="raise").astype("int64")
        loaded["lifeExp"] = pd.to_numeric(loaded["lifeExp"], errors="raise").astype("float64")
        loaded["gdpPercap"] = pd.to_numeric(loaded["gdpPercap"], errors="raise").astype("float64")
        same = len(loaded) == len(canonical)
        for col in ["country","continent","year","pop"]:
            same = same and loaded[col].equals(canonical[col].reset_index(drop=True))
        for col in ["lifeExp","gdpPercap"]:
            same = same and np.allclose(loaded[col], canonical[col], atol=atol, rtol=0)
        checks.append({"check":f"{suffix}_round_trip","expected":len(canonical),"actual":len(loaded),"tolerance":atol,"pass":bool(same)})
        if not same:
            raise ValueError(f"Export round-trip comparison failed: canonical.{suffix}")
    return checks

def promote_staging(staging: Path, output: Path) -> None:
    """Replace successful outputs only after the staged run has passed."""
    backup = output.with_name(output.name + "_previous")
    if backup.exists(): shutil.rmtree(backup)
    if output.exists(): output.rename(backup)
    try:
        staging.rename(output)
    except Exception:
        if backup.exists() and not output.exists(): backup.rename(output)
        raise
    if backup.exists(): shutil.rmtree(backup)
