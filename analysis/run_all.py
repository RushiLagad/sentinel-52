#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09; the clean-clone
# guard and the default integrity check added 2026-10-27.
# -----------------------------------------------------------------------------
"""Run the whole pipeline in order. Works the same on Windows, macOS and Linux.

The data is not in the repository, so get it first. See the README; the short
version is: download the 31 FSIS files listed by

    python scripts/01_fetch_fsis.py --print-urls

into data/raw/<folder>/<name>, then:

  python run_all.py                      # verifies data/raw, then builds everything
  python run_all.py --download           # convenience: try fetching from FSIS first
  python run_all.py --from-bundle X.zip  # from a saved bundle of the same files
  python run_all.py --skip-verify        # skip the SHA-256 check (not recommended)

Whichever route you take, every file is checked against the SHA-256 in
data/MANIFEST.json before anything is built. Total runtime is about three
minutes on one core.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S = ROOT / "scripts"
REPO = ROOT.parent                      # repository root; data/ lives there, outputs/ stays under analysis/
RAW, PROC, VALID = str(REPO / "data" / "raw"), str(REPO / "data" / "processed"), str(REPO / "data" / "validation")
MANIFEST = str(REPO / "data" / "MANIFEST.json")
DECISION_H = "3"                        # the decision layer's horizon; see the comment at its call
VULN = REPO / "data" / "vulnerability" / "vulnerability_county.csv"
INV = REPO / "data" / "inventory"

NO_DATA = """
data/raw is empty, so there is nothing to build.

The 31 FSIS source files are not committed to this repository: they are 62 MB of
federal open data and they belong to FSIS, not to us. Get them like this.

  1. List what to download and where each file goes:

         cd analysis
         python scripts/01_fetch_fsis.py --print-urls

  2. Download those 31 files into data/raw/<folder>/<name>. The four folders are
     raw_poultry, narms_cecal, establishments and salmonella_categories. Landing
     pages for the human route are in the README; every direct URL is in
     data/MANIFEST.json.

  3. Verify and build:

         python run_all.py

You can also try `python run_all.py --download`, which fetches the files over the
network. That is a convenience and it is not reliable: as of 2026-10-27 the FSIS
CDN returns HTTP 403 to automated requests, even though the files are unchanged
and still public at the URLs in the manifest. If that happens, use the manual
route above. The SHA-256 check is identical either way, so a manual download is
not a weaker provenance claim.
""".rstrip()


def run(*args: str) -> None:
    t = time.time()
    print("\n" + "=" * 100 + "\n$ python " + " ".join(args) + "\n" + "=" * 100, flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)
    print(f"[{time.time() - t:.0f}s]", flush=True)


def raw_is_populated() -> bool:
    p = Path(RAW)
    return p.is_dir() and any(f.is_file() and f.name != "MANIFEST.json" for f in p.rglob("*"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-bundle", type=Path); ap.add_argument("--download", action="store_true")
    ap.add_argument("--skip-verify", action="store_true", help="do not hash-check data/raw before building")
    ap.add_argument("--horizons", default="6,3,12", help="early-warning horizons in months; the first one is the headline")
    a = ap.parse_args()

    if a.from_bundle:
        run(str(S / "01_fetch_fsis.py"), "--from-bundle", str(a.from_bundle), "--raw", RAW, "--manifest", MANIFEST)
    elif a.download:
        try:
            run(str(S / "01_fetch_fsis.py"), "--raw", RAW, "--manifest", MANIFEST)
        except subprocess.CalledProcessError:
            if not raw_is_populated():
                print(NO_DATA); raise SystemExit(1)
            print("\n--download did not complete, but data/raw is populated; verifying what is there.")
            a.skip_verify = False
    elif not raw_is_populated():
        print(NO_DATA); raise SystemExit(1)
    elif not a.skip_verify:
        run(str(S / "01_fetch_fsis.py"), "--verify-only", "--raw", RAW, "--manifest", MANIFEST)

    run(str(S / "02_build_tables.py"), "--raw", RAW, "--out", PROC)
    run(str(S / "03_profile.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "04_validate_categories.py"), "--data", PROC, "--posted-dir", VALID, "--out", "outputs")
    hs = [h.strip() for h in a.horizons.split(",") if h.strip()]
    # The decision layer needs this horizon's scores, so make sure it gets built
    # even if the caller did not ask for it.
    if DECISION_H not in hs:
        hs.append(DECISION_H)
        print(f"added horizon {DECISION_H} to the loop: the decision layer runs at it")
    for h in hs:
        run(str(S / "05_early_warning_baseline.py"), "--data", PROC, "--out", "outputs", "--horizon", h)
        run(str(S / "05c_calibration.py"), "--out", "outputs", "--horizon", h)
        run(str(S / "05d_ablation.py"), "--data", PROC, "--out", "outputs", "--horizon", h)
    run(str(S / "05b_watchlist_comparison.py"), "--data", PROC, "--out", "outputs", "--horizon", hs[0])
    run(str(S / "06_hazard_first_look.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "07_figures.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "08_key_numbers.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "18_figure_system_map.py"), "--out", "outputs")
    # Regenerated every run so it cannot drift from the tables it documents.
    # Exits non-zero if any column lacks a description, which fails the run
    # rather than shipping a dictionary with holes in it.
    run(str(S / "19_build_data_dictionary.py"), "--repo", str(REPO))

    # The decision layer needs the county vulnerability file, which comes from
    # 13_fetch_vulnerability.py and needs the network. Skipped with a reason
    # rather than failing the run, so the FSIS analysis above still completes
    # for anyone who cannot reach svi.cdc.gov.
    if VULN.exists():
        run(str(S / "14_build_synthetic_inventory.py"), "--data", PROC,
            "--vulnerability", str(VULN), "--out", str(INV))
        # Pinned to 3 months, NOT to hs[0]. The decision is made inside a lot's
        # perishability window, which is weeks, so the nearest forecast horizon
        # is the right one. Using hs[0] silently ran this at 6 months whenever
        # --horizons started with 6, which is the default.
        run(str(S / "16_decision_layer.py"),
            "--lots", str(INV / "lots_synthetic.csv"),
            "--scores", f"outputs/early_warning_test_scores_h{DECISION_H}.parquet",
            "--out", "outputs", "--horizon", DECISION_H)
    else:
        print(f"\nSkipping the decision layer: {VULN} is not there.")
        print("  Build it first, which needs network access to svi.cdc.gov:")
        print(f"      python scripts/13_fetch_vulnerability.py --out {VULN.parent}")
        print("  Everything above this line is complete and does not depend on it.")

    print(f"\nDone. Tables and figures are in {ROOT / 'outputs'}, tidy data in {PROC}.")


if __name__ == "__main__":
    main()
