#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09.
# Tested: --from-bundle on the real bundle, and the download path against a
# local copy of the files. NOT yet run against fsis.usda.gov itself, because the
# workspace it was written in cannot reach that site. Run it once and check.
# -----------------------------------------------------------------------------
"""Get the original FSIS files into data/raw and verify them.

Two ways to use it:

  1) Unpack the bundle made on 2026-10-09 (original FSIS files, unmodified):
       python scripts/01_fetch_fsis.py --from-bundle fsis_sensd_raw_2026-10-09.zip --raw data/raw

  2) Download straight from FSIS (use this on the hub, or to refresh the data):
       python scripts/01_fetch_fsis.py --raw data/raw

Every file is compared with the SHA-256 recorded in MANIFEST.json. FSIS replaces
the current fiscal-year file every quarter and the establishment directory every
week, so a mismatch on those usually means "FSIS posted a newer version", not
corruption. The script reports it and keeps going; re-run 02 to 05 afterwards
and expect small changes in the numbers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://www.fsis.usda.gov/sites/default/files/media_file/documents/"
FILES: list[tuple[str, str]] = (
    [("raw_poultry", f"raw_poultry_sampling_data_fy{y}.zip") for y in range(2014, 2027)]
    + [("narms_cecal", f"fsis_narms_cecal_sampling_fy{y}.zip") for y in range(2014, 2027)]
    + [("establishments", n) for n in ("MPI_Directory_by_Establishment_Number.csv", "Dataset_Establishment_Demographic_Data.csv",
                                       "MPI_Inactive_Directory_by_Establishment_Number.csv")]
    + [("salmonella_categories", n) for n in ("Dataset_EstablishmentCategories_202609_0.xlsx", "Dataset_EstablishmentCategoriesAggregate_202609_0.xlsx")]
)
UA = "Mozilla/5.0 (research; NAFSI Hub Student Data Challenge team) Python-urllib"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, retries: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, tmp.open("wb") as fh:
                shutil.copyfileobj(r, fh)
            tmp.replace(dest)
            return
        except Exception as e:  # noqa: BLE001  (report and retry)
            print(f"   attempt {attempt} failed: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"could not download {url}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--from-bundle", type=Path, help="zip made by the browser download on 2026-10-09")
    ap.add_argument("--manifest", type=Path, default=Path("data/MANIFEST.json"), help="expected hashes (snapshot of 2026-10-09)")
    ap.add_argument("--base-url", default=BASE, help="override for testing")
    ap.add_argument("--force", action="store_true", help="download even if the file is already there")
    a = ap.parse_args()
    a.raw.mkdir(parents=True, exist_ok=True)

    if a.from_bundle:
        with zipfile.ZipFile(a.from_bundle) as z:
            for info in z.infolist():
                target = (a.raw / info.filename).resolve()
                if not str(target).startswith(str(a.raw.resolve())):      # never write outside data/raw
                    raise RuntimeError(f"unsafe path in bundle: {info.filename}")
            z.extractall(a.raw)
        print(f"unpacked {a.from_bundle} into {a.raw}")
    else:
        for folder, name in FILES:
            dest = a.raw / folder / name
            if dest.exists() and not a.force:
                print(f"have   {folder}/{name}")
                continue
            print(f"get    {folder}/{name}")
            download(a.base_url + name, dest)

    man_path = a.manifest if a.manifest.exists() else a.raw / "MANIFEST.json"
    if not man_path.exists():
        print("no MANIFEST.json found, skipping hash check"); return 0
    expected = {f["path"]: f for f in json.loads(man_path.read_text())["files"]}
    same = newer = missing = 0
    for folder, name in FILES:
        rel = f"{folder}/{name}"; p = a.raw / rel
        if not p.exists():
            print(f"MISSING  {rel}"); missing += 1; continue
        if rel in expected and sha256(p) == expected[rel]["sha256"]:
            same += 1
        else:
            newer += 1; print(f"DIFFERS  {rel}  (not the 2026-10-09 snapshot; FSIS may have posted an update)")
    print(f"\n{same} files match the 2026-10-09 snapshot, {newer} differ, {missing} missing")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
