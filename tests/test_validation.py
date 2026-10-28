import pandas as pd
from src.validator import validate_records

YEARS = [1952, 1957, 1962, 1967, 1972, 1977, 1982, 1987, 1992, 1997, 2002, 2007]
CONTINENTS = ["Africa", "Americas", "Asia", "Europe", "Oceania"]

def valid_row():
    return {"country":"Testland","continent":"Asia","year":2007,"lifeExp":70.0,"pop":1000,"gdpPercap":500.0}

def test_invalid_rows_are_quarantined_before_integer_cast():
    rows = [valid_row(), {**valid_row(), "country":""}, {**valid_row(), "year":"bad"},
            {**valid_row(), "year":2007.5}, {**valid_row(), "pop":1000.5},
            {**valid_row(), "lifeExp":float("inf")}, {**valid_row(), "pop":-1}]
    result = validate_records(pd.DataFrame(rows), "fixture.csv", YEARS, CONTINENTS)
    assert len(result.valid) == 1
    assert len(result.quarantine) == 6
    assert result.quarantine["source_record"].tolist() == [2,3,4,5,6,7]

def test_missing_key_and_out_of_range_values_fail_row_validation():
    rows = [valid_row(), {**valid_row(), "year":None}, {**valid_row(), "continent":"Atlantis"},
            {**valid_row(), "lifeExp":-1}, {**valid_row(), "gdpPercap":0}]
    result = validate_records(pd.DataFrame(rows), "fixture.csv", YEARS, CONTINENTS)
    assert len(result.valid) == 1
    assert len(result.quarantine) == 4
