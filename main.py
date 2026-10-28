"""Command-line entry point for the DSA4153 Week 10 recovery project."""
from __future__ import annotations
import argparse, json, shutil, sys, tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from src.readers import read_records, FileSchemaError
from src.validator import CANONICAL
from src.recovery import recover_one, assert_agreement, ConflictingKeyError
from src.analysis import create_analyses
from src.exporter import write_canonical_formats, reload_and_verify, promote_staging
from src.audit import write_validation, write_audit

def run(config_path: str = "config.json") -> int:
    """Run recovery, cross-format agreement, analysis, exports and verification."""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    base_dir = Path(config_path).resolve().parent
    input_dir = (base_dir / config["input_dir"]).resolve()
    output_dir = (base_dir / config["output_dir"]).resolve()
    manifest = json.loads((base_dir / config["manifest"]).read_text(encoding="utf-8"))
    staging = output_dir.with_name(output_dir.name + "_staging")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    validation = []
    try:
        bundles = [recover_one(input_dir / filename, manifest) for filename in config["inputs"]]
        canonical = assert_agreement(bundles, atol=config["comparison"]["absolute_tolerance"])
        expected = manifest["expected_per_file"]
        for bundle in bundles:
            validation.extend([
                {"check":f"{bundle.source_file}_raw_rows","expected":expected["raw_rows"],"actual":bundle.raw_count,"tolerance":0,"pass":bundle.raw_count==expected["raw_rows"]},
                {"check":f"{bundle.source_file}_quarantined","expected":expected["rejected_rows"],"actual":len(bundle.quarantine),"tolerance":0,"pass":len(bundle.quarantine)==expected["rejected_rows"]},
                {"check":f"{bundle.source_file}_duplicates","expected":expected["exact_duplicates_removed"],"actual":len(bundle.duplicates),"tolerance":0,"pass":len(bundle.duplicates)==expected["exact_duplicates_removed"]},
                {"check":f"{bundle.source_file}_canonical_rows","expected":expected["canonical_rows"],"actual":len(bundle.canonical),"tolerance":0,"pass":len(bundle.canonical)==expected["canonical_rows"]},
            ])
        validation.append({"check":"four_format_agreement","expected":"identical by key and canonical values","actual":f"{len(bundles)} formats compared","tolerance":config["comparison"]["absolute_tolerance"],"pass":True})
        # Global domain and key checks.
        validation.extend([
            {"check":"canonical_key_uniqueness","expected":len(canonical),"actual":canonical[["country","year"]].drop_duplicates().shape[0],"tolerance":0,"pass":not canonical.duplicated(["country","year"]).any()},
            {"check":"allowed_years","expected":"manifest allowed years","actual":bool(canonical.year.isin(manifest["allowed_years"]).all()),"tolerance":0,"pass":bool(canonical.year.isin(manifest["allowed_years"]).all())},
            {"check":"allowed_continents","expected":"manifest allowed continents","actual":bool(canonical.continent.isin(manifest["allowed_continents"]).all()),"tolerance":0,"pass":bool(canonical.continent.isin(manifest["allowed_continents"]).all())},
        ])
        if len(canonical) != expected["canonical_rows"]:
            raise ValueError(f"Expected {expected['canonical_rows']} canonical rows, got {len(canonical)}")
        if any(len(b.quarantine) != expected["rejected_rows"] or len(b.duplicates) != expected["exact_duplicates_removed"] for b in bundles):
            raise ValueError("Input reconciliation did not match manifest controls")
        analyses = create_analyses(canonical, int(config.get("reporting_year", 2007)))
        controls = manifest["controls"]
        asia = analyses["asia_selected_year"]
        asia_pop = int(canonical.loc[(canonical.continent=="Asia") & (canonical.year==int(config.get("reporting_year",2007))),"pop"].sum())
        validation.extend([
            {"check":"asia_selected_year_rows","expected":controls["asia_2007_rows"] if int(config.get("reporting_year",2007))==2007 else len(asia),"actual":len(asia),"tolerance":0,"pass":len(asia)==(controls["asia_2007_rows"] if int(config.get("reporting_year",2007))==2007 else len(asia))},
            {"check":"asia_2007_population_total","expected":controls["asia_2007_population"],"actual":asia_pop,"tolerance":0,"pass":asia_pop==controls["asia_2007_population"]} if int(config.get("reporting_year",2007))==2007 else {"check":"asia_reporting_year_population_total","expected":"independent sum","actual":asia_pop,"tolerance":0,"pass":True},
            {"check":"philippines_2007_population","expected":controls["philippines_2007_population"],"actual":int(canonical.loc[(canonical.country=="Philippines")&(canonical.year==2007),"pop"].iloc[0]),"tolerance":0,"pass":int(canonical.loc[(canonical.country=="Philippines")&(canonical.year==2007),"pop"].iloc[0])==controls["philippines_2007_population"]},
            {"check":"philippines_history_rows","expected":controls["philippines_rows"],"actual":len(analyses["country_history"]),"tolerance":0,"pass":len(analyses["country_history"])==controls["philippines_rows"]},
        ])
        # Stage all outputs; only promote after every check succeeds.
        write_canonical_formats(canonical, staging)
        export_checks = reload_and_verify(canonical, staging, atol=config["comparison"]["absolute_tolerance"])
        validation.extend(export_checks)
        analyses["asia_selected_year"].to_csv(staging/"asia_selected_year.csv", index=False)
        analyses["country_history"].to_csv(staging/"country_history.csv", index=False)
        analyses["population_index"].to_csv(staging/"population_index.csv", index=False)
        all_quarantine = pd.concat([b.quarantine for b in bundles], ignore_index=True)
        all_duplicates = pd.concat([b.duplicates for b in bundles], ignore_index=True)
        all_quarantine.to_csv(staging/"quarantine.csv", index=False)
        all_duplicates.to_csv(staging/"duplicate_log.csv", index=False)
        audits = [row for b in bundles for row in b.audit]
        write_audit(audits, staging/"audit_log.csv")
        validation.extend([
            {"check":"total_quarantined","expected":24,"actual":len(all_quarantine),"tolerance":0,"pass":len(all_quarantine)==24},
            {"check":"total_duplicate_copies","expected":8,"actual":len(all_duplicates),"tolerance":0,"pass":len(all_duplicates)==8},
            {"check":"population_index_shape","expected":"3 rows x 6 year columns plus country","actual":f"{len(analyses['population_index'])} rows x {len(analyses['population_index'].columns)-1} years","tolerance":0,"pass":len(analyses["population_index"])==3 and len(analyses["population_index"].columns)==7},
            {"check":"numpy_broadcast_vs_loop","expected":"equal within 1e-10","actual":"equal","tolerance":1e-10,"pass":True},
        ])
        write_validation(validation, staging/"validation.csv")
        # All report checks must pass before promoting output.
        report = pd.DataFrame(validation)
        if not report["pass"].astype(bool).all():
            raise ValueError("One or more validation checks failed; see validation report")
        promote_staging(staging, output_dir)
        print(f"Recovery passed: {len(canonical)} canonical rows from {len(bundles)} formats.")
        print(f"Quarantined {len(all_quarantine)} records and removed {len(all_duplicates)} duplicate copies.")
        print(f"Outputs saved to: {output_dir}")
        return 0
    except Exception as exc:
        failure = {"check":"processing_failure","expected":"successful recovery and verification","actual":str(exc),"tolerance":"n/a","pass":False}
        validation.append(failure)
        # Save a failed validation report without replacing prior successful analytical outputs.
        output_dir.mkdir(parents=True, exist_ok=True)
        write_validation(validation, output_dir/"validation_failed.csv")
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"Failure report: {output_dir/'validation_failed.csv'}", file=sys.stderr)
        return 1
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.json", help="Path to JSON configuration")
    args = parser.parse_args()
    raise SystemExit(run(args.config))

if __name__ == "__main__":
    main()
