# DSA4153 Week 10 Group Project — Four-Format Data Recovery

## Project goal
Recover the same clean historical Gapminder dataset from CSV, XLSX, nested JSON, and Parquet; validate records; quarantine invalid rows; remove exact duplicates; stop on conflicting `(country, year)` keys; compare formats; perform pandas and NumPy analysis; export and verify results.

The input observations cover **1952–2007**. They are historical data, not current conditions. The supplied defects are classroom fixtures, not errors attributed to the original Gapminder source.

## Team ownership (complete before submission)
Replace the placeholders below with the actual five members and Git identities. Each member must author a substantive processing function/method and an automated check, work on a named branch, and review another member's work.

| Member | Git identity | Responsibility |
|---|---|---|
| Member 1 | TO_FILL | CSV/Excel readers, configuration, reader tests |
| Member 2 | TO_FILL | JSON/Parquet readers, mapping, normalization tests |
| Member 3 | TO_FILL | Validation, quarantine, duplicates/conflicts, tests |
| Member 4 | TO_FILL | pandas analysis, NumPy matrix, calculation tests |
| Member 5 | TO_FILL | exports/round trips, staging, CLI/audit, failure tests |

## Repository layout
- `main.py`: command-line orchestration.
- `config.json`: input/output paths, reporting year, comparison tolerances.
- `data/raw/`: original supplied inputs and manifest; preserve their bytes.
- `src/`: reusable reader, validation, recovery, analysis, export, and audit code.
- `tests/`: automated checks.
- `outputs/`: generated deliverables. This folder is ignored by Git by default but should be included in the final group ZIP.
- `notebooks/report.ipynb`: imports and demonstrates the project code; `notebooks/report.html` is its HTML export.
- `contributions.csv`, `reviews.md`, `submission_manifest.txt`: evidence required by the assignment.

## Setup
Use Python 3.10+ (or a version compatible with the installed dependencies).

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the program
From the repository root:

```bash
python main.py --config config.json
```

The default reporting year is 2007. To change it to 1997, edit `"reporting_year": 1997` in `config.json` and rerun. Processing functions do not need to be edited.

The program stages generated files and only promotes them to `outputs/` after recovery, cross-format agreement, and export round-trip checks pass. A failed run returns a nonzero exit code and writes `outputs/validation_failed.csv` without replacing a previously successful output set.

## Run tests

```bash
python -m pytest -v
```

Tests cover normal format reading, schema failures, missing files, invalid numeric values, non-finite and fractional values, invalid domains, duplicates, conflicting keys, reordered rows, analysis controls, export round trips, and corrupted exports.

## Expected reconciliation
For each normal input: `1,712 raw = 6 quarantined + 2 exact duplicate copies removed + 1,704 canonical rows`.

Across all four inputs: **24 quarantined records**, **8 duplicate copies removed**, and **1,704 canonical observations**. The four format versions must agree; do not concatenate them into 6,816 observations.

For the default 2007 analysis, the manifest controls include 33 Asian rows, Asian population total `3,811,953,827`, and Philippine population `91,077,287`.

## Required generated files
`outputs/` should contain:
- `canonical.csv`, `canonical.xlsx` (sheet `observations`), `canonical.json` (records orientation), `canonical.parquet`
- `asia_selected_year.csv`, `country_history.csv`, `population_index.csv`
- `quarantine.csv`, `duplicate_log.csv`, `validation.csv`, `audit_log.csv`, `test_results.txt`

The final ZIP must also include the supplied `data/` folder, source code, tests, notebook and HTML export, contribution/review evidence, and submission manifest.

## Git workflow and release
1. Create a branch per member, e.g. `member1-csv-excel`.
2. Each member commits a real processing function/method and an automated test.
3. Open pull requests; record reviewed commit, specific feedback, and response in `reviews.md`.
4. Merge reviewed work while preserving individual commit history.
5. Have a member other than the integrator clone the repository fresh and follow these instructions.
6. Tag the submitted version `week10-v1.0`.
7. Record the tag's **full commit hash** and repository URL in `submission_manifest.txt`.

## Before submission
Replace all `TO_FILL` placeholders. Verify the actual commits and review references; never invent commit hashes or Git identities. Run the program and all tests in the submission environment, inspect generated reports, and follow the course AI policy/disclose assistance as required.
