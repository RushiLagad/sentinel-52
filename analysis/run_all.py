#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09.
# -----------------------------------------------------------------------------
"""Run the whole pipeline in order. Works the same on Windows, macOS and Linux.

  python run_all.py --from-bundle path/to/fsis_sensd_raw_2026-10-09.zip   # from a saved bundle of the FSIS files
  python run_all.py --download                                            # or pull the files from FSIS
  python run_all.py                                                       # data/raw already in place
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


def run(*args: str) -> None:
    t = time.time()
    print("\n" + "=" * 100 + "\n$ python " + " ".join(args) + "\n" + "=" * 100, flush=True)
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)
    print(f"[{time.time() - t:.0f}s]", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-bundle", type=Path); ap.add_argument("--download", action="store_true")
    ap.add_argument("--horizons", default="6,3,12", help="early-warning horizons in months; the first one is the headline")
    a = ap.parse_args()
    if a.from_bundle:
        run(str(S / "01_fetch_fsis.py"), "--from-bundle", str(a.from_bundle), "--raw", RAW, "--manifest", MANIFEST)
    elif a.download:
        run(str(S / "01_fetch_fsis.py"), "--raw", RAW, "--manifest", MANIFEST)
    run(str(S / "02_build_tables.py"), "--raw", RAW, "--out", PROC)
    run(str(S / "03_profile.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "04_validate_categories.py"), "--data", PROC, "--posted-dir", VALID, "--out", "outputs")
    hs = [h.strip() for h in a.horizons.split(",") if h.strip()]
    for h in hs:
        run(str(S / "05_early_warning_baseline.py"), "--data", PROC, "--out", "outputs", "--horizon", h)
        run(str(S / "05c_calibration.py"), "--out", "outputs", "--horizon", h)
        run(str(S / "05d_ablation.py"), "--data", PROC, "--out", "outputs", "--horizon", h)
    run(str(S / "05b_watchlist_comparison.py"), "--data", PROC, "--out", "outputs", "--horizon", hs[0])
    run(str(S / "06_hazard_first_look.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "07_figures.py"), "--data", PROC, "--out", "outputs")
    run(str(S / "08_key_numbers.py"), "--data", PROC, "--out", "outputs")
    print(f"\nDone. Tables and figures are in {ROOT / 'outputs'}, tidy data in {PROC}.")


if __name__ == "__main__":
    main()
