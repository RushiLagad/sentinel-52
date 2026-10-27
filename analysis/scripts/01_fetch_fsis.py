#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09; the manual
# download and verify paths added 2026-10-27 after the FSIS CDN began returning
# HTTP 403 to automated requests.
# Tested: --from-bundle on the real bundle; --verify-only against all 31 real
# files; the download path run against fsis.usda.gov on 2026-10-27, where it
# returns 403 for every file. The files themselves are unchanged and still
# public at the URLs in MANIFEST.json, checked in a browser the same day.
# -----------------------------------------------------------------------------
"""Get the original 31 FSIS files into data/raw and verify them.

The verification is the point of this script. Getting the bytes is the easy part
and can be done any way you like; what matters is that what you have is what this
analysis was run on. So the recommended route is manual download, then verify:

  1) MANUAL (recommended). Print what to get and where to put it:
       python scripts/01_fetch_fsis.py --print-urls
     Download those 31 files into data/raw/<folder>/<name>, then check them:
       python scripts/01_fetch_fsis.py --verify-only --raw data/raw
     Neither command touches the network. Landing pages are in the README.

  2) AUTOMATED (convenience, may fail). Fetch straight from fsis.usda.gov:
       python scripts/01_fetch_fsis.py --raw data/raw
     As of 2026-10-27 the FSIS CDN returns HTTP 403 to this script even though
     the files are still public and unchanged at the URLs in MANIFEST.json. The
     files are fine; the CDN declines the request. Use route 1 when this happens.

  3) From a local bundle of the same files, if someone sent you one:
       python scripts/01_fetch_fsis.py --from-bundle fsis_sensd_raw_2026-10-09.zip --raw data/raw

All three routes end in the same SHA-256 check against data/MANIFEST.json. FSIS
replaces the current fiscal-year file every quarter and the establishment
directory every week, so a mismatch on those usually means "FSIS posted a newer
version", not corruption. The script reports which files differ and keeps going;
re-run 02 onwards afterwards and expect small changes in the numbers.
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

REPO = Path(__file__).resolve().parents[2]      # <repo>/analysis/scripts/01_fetch_fsis.py
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
    raise RuntimeError(
        f"could not download {url}\n"
        "\n"
        "  The file is almost certainly still public; the FSIS CDN declines automated\n"
        "  requests (HTTP 403 as of 2026-10-27). Download the 31 files by hand instead:\n"
        "\n"
        "      python scripts/01_fetch_fsis.py --print-urls\n"
        "\n"
        "  then put them under data/raw/<folder>/<name> and verify:\n"
        "\n"
        "      python scripts/01_fetch_fsis.py --verify-only --raw data/raw\n"
        "\n"
        "  The SHA-256 check is identical either way, so a manual download is not a\n"
        "  weaker provenance claim than an automated one."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", type=Path, default=REPO / "data" / "raw",
                    help="where the FSIS files live (default: the repo's data/raw, whatever directory you run from)")
    ap.add_argument("--from-bundle", type=Path, help="zip made by the browser download on 2026-10-09")
    ap.add_argument("--manifest", type=Path, default=REPO / "data" / "MANIFEST.json",
                    help="expected hashes, snapshot of 2026-10-09 (default: the repo's data/MANIFEST.json)")
    ap.add_argument("--base-url", default=BASE, help="override for testing")
    ap.add_argument("--force", action="store_true", help="download even if the file is already there")
    ap.add_argument("--verify-only", action="store_true",
                    help="hash-check the files already in --raw; never touches the network")
    ap.add_argument("--print-urls", action="store_true",
                    help="print the 31 source URLs and their destinations, then exit; never touches the network")
    a = ap.parse_args()

    if a.print_urls:
        man_path = a.manifest if a.manifest.exists() else a.raw / "MANIFEST.json"
        urls = {}
        if man_path.exists():
            urls = {f["path"]: f["source_url"] for f in json.loads(man_path.read_text())["files"]}
        print(f"# {len(FILES)} FSIS source files. Save each one at {a.raw}/<path>.")
        print(f"# destination path{chr(9)}source url")
        for folder, name in FILES:
            rel = f"{folder}/{name}"
            print(f"{rel}\t{urls.get(rel, a.base_url + name)}")
        print(f"\n# then: python scripts/01_fetch_fsis.py --verify-only --raw {a.raw}")
        return 0

    a.raw.mkdir(parents=True, exist_ok=True)

    if a.verify_only:
        print(f"verifying the files already in {a.raw}; not contacting fsis.usda.gov")
    elif a.from_bundle:
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
        print(f"\nERROR: no manifest at {a.manifest} or {a.raw / 'MANIFEST.json'}, so nothing can be")
        print("verified. data/MANIFEST.json is committed to this repository; pass --manifest if")
        print("you have moved it. Refusing to report success without checking the hashes.")
        return 2
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
