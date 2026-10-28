"""Row-level validation with a result object for accepted and quarantined records."""
from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Any
import numpy as np
import pandas as pd

CANONICAL = ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]
STRING_COLUMNS = ["country", "continent"]
NUMERIC_COLUMNS = ["year", "lifeExp", "pop", "gdpPercap"]

@dataclass
class ValidationResult:
    """Accepted canonical rows and rejected source rows with reasons."""
    valid: pd.DataFrame
    quarantine: pd.DataFrame

def validate_records(df: pd.DataFrame, source_file: str, allowed_years: list[int],
                     allowed_continents: list[str]) -> ValidationResult:
    """Validate raw field values before casting integer columns."""
    accepted, rejected = [], []
    for record_no, (_, row) in enumerate(df.iterrows(), start=1):
        original = {col: row.get(col) for col in CANONICAL}
        reasons = []
        country = "" if pd.isna(original["country"]) else str(original["country"]).strip()
        continent = "" if pd.isna(original["continent"]) else str(original["continent"]).strip()
        if not country: reasons.append("empty_country")
        if not continent: reasons.append("empty_continent")
        elif continent not in allowed_continents: reasons.append("invalid_continent")

        parsed: dict[str, Any] = {}
        for col in NUMERIC_COLUMNS:
            raw = original[col]
            try:
                val = float(raw)
                if not math.isfinite(val):
                    reasons.append(f"non_finite_{col}")
                else:
                    parsed[col] = val
            except (TypeError, ValueError):
                reasons.append(f"missing_or_unparseable_{col}")

        if "year" in parsed and math.isfinite(parsed["year"]):
            if not parsed["year"].is_integer(): reasons.append("fractional_year")
            elif int(parsed["year"]) not in allowed_years: reasons.append("year_out_of_range")
        if "lifeExp" in parsed and math.isfinite(parsed["lifeExp"]):
            if not (0 < parsed["lifeExp"] <= 120): reasons.append("lifeExp_out_of_range")
        if "pop" in parsed and math.isfinite(parsed["pop"]):
            if not parsed["pop"].is_integer(): reasons.append("fractional_population")
            elif parsed["pop"] <= 0: reasons.append("population_out_of_range")
        if "gdpPercap" in parsed and math.isfinite(parsed["gdpPercap"]):
            if parsed["gdpPercap"] <= 0: reasons.append("gdpPercap_out_of_range")

        if reasons:
            rejected.append({
                "source_file": source_file, "source_record": record_no,
                "reason": ";".join(dict.fromkeys(reasons)),
                **original
            })
        else:
            accepted.append({
                "country": country, "continent": continent,
                "year": int(parsed["year"]), "lifeExp": float(parsed["lifeExp"]),
                "pop": int(parsed["pop"]), "gdpPercap": float(parsed["gdpPercap"])
            })
    valid = pd.DataFrame(accepted, columns=CANONICAL)
    quarantine = pd.DataFrame(rejected, columns=["source_file","source_record","reason",*CANONICAL])
    return ValidationResult(valid, quarantine)
