"""Pandas and NumPy analyses for the recovered canonical table."""
from __future__ import annotations
import numpy as np
import pandas as pd

def create_analyses(canonical: pd.DataFrame, reporting_year: int) -> dict[str, pd.DataFrame]:
    """Build the three required analytical CSV tables."""
    asia = canonical.loc[(canonical["continent"] == "Asia") & (canonical["year"] == reporting_year)].copy()
    asia["population_millions"] = asia["pop"] / 1_000_000
    asia["lifeExp_rank"] = asia["lifeExp"].rank(method="min", ascending=False).astype("int64")
    asia = asia.sort_values(["lifeExp_rank","country"]).reset_index(drop=True)

    phil = canonical.loc[canonical["country"] == "Philippines"].copy().sort_values("year")
    if not phil.empty:
        phil["population_millions"] = phil["pop"] / 1_000_000
        phil["lifeExp_change_from_first"] = phil["lifeExp"] - phil["lifeExp"].iloc[0]
    phil = phil.reset_index(drop=True)

    countries = ["Philippines", "Indonesia", "Thailand"]
    years = [1982, 1987, 1992, 1997, 2002, 2007]
    subset = canonical.loc[canonical["country"].isin(countries) & canonical["year"].isin(years),
                           ["country","year","pop"]]
    matrix = subset.pivot(index="country", columns="year", values="pop").reindex(index=countries, columns=years)
    values = matrix.to_numpy(dtype=np.float64)
    baseline = values[:, [0]]
    indexed = np.broadcast_to(values / baseline * 100, values.shape).copy()
    # Independent loop check, intentionally separate from broadcast calculation.
    loop = np.empty_like(indexed)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            loop[i, j] = values[i, j] / values[i, 0] * 100
    if not np.allclose(indexed, loop, atol=1e-10, rtol=0):
        raise AssertionError("NumPy broadcast and loop calculations disagree")
    pop_index = pd.DataFrame(indexed, columns=[str(y) for y in years])
    pop_index.insert(0, "country", countries)
    pop_index.attrs["matrix_shape_before_broadcast"] = list(values.shape)
    pop_index.attrs["baseline_shape"] = list(baseline.shape)
    pop_index.attrs["matrix_shape_after_broadcast"] = list(indexed.shape)
    # Boolean selection and aggregation demonstration.
    selected = values[values > 0]
    pop_index.attrs["boolean_selected_population_count"] = int(selected.size)
    pop_index.attrs["selected_population_sum"] = int(selected.sum())
    return {"asia_selected_year": asia, "country_history": phil, "population_index": pop_index}
