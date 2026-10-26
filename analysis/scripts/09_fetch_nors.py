#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26. Review before
# relying on it.
# -----------------------------------------------------------------------------
"""Fetch NORS outbreak aggregates from CDC's public open-data portal.

NORS (National Outbreak Reporting System) is published by CDC at
https://data.cdc.gov/dataset/NORS/5xkq-dg7x under the Socrata Open Data API.
This script pulls server-side aggregates rather than the full table, because the
analysis only needs counts by year, IFSAC food category and serotype.

The challenge organisers also circulated a NORS extract by email under a
no-redistribution condition. That file is deliberately NOT used here and is NOT
in this repository. Everything below comes from the public endpoint, so the
pipeline is reproducible by anyone without special access.

Usage:
  python scripts/09_fetch_nors.py --out data/nors
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://data.cdc.gov/resource/5xkq-dg7x.json"
# Salmonella, foodborne, over the years that overlap the FSIS sampling data.
WHERE_SALM = (
    "etiology like '%Salmonella%' AND primary_mode='Food' "
    "AND year>='{y0}' AND year<='{y1}'"
)
POULTRY = "('Chicken','Turkey','Other Poultry','Eggs')"


def soql(params: dict, timeout: int = 60) -> list[dict]:
    url = BASE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def write_csv(path: Path, rows: list[dict], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({c: row.get(c, "") for c in cols})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--y0", default="2014")
    ap.add_argument("--y1", default="2023", help="public NORS currently ends at 2023")
    a = ap.parse_args()
    where = WHERE_SALM.format(y0=a.y0, y1=a.y1)

    try:
        poultry = soql({
            "$select": ("year,ifsac_category as cat,serotype_or_genotype as sero,"
                        "count(1) as nb,sum(illnesses) as ill,"
                        "sum(hospitalizations) as hosp,sum(deaths) as dth"),
            "$where": f"{where} AND ifsac_category in {POULTRY}",
            "$group": "year,ifsac_category,serotype_or_genotype",
            "$limit": "2000",
        })
        attribution = soql({
            "$select": ("ifsac_category as cat,count(1) as nb,sum(illnesses) as ill,"
                        "sum(hospitalizations) as hosp,sum(deaths) as dth"),
            "$where": where,
            "$group": "ifsac_category",
            "$limit": "100",
        })
    except Exception as exc:  # noqa: BLE001
        print(f"NORS fetch failed: {exc}", file=sys.stderr)
        print("The cached aggregates in data/nors/ were produced by this same query "
              "and let the rest of the pipeline run offline.", file=sys.stderr)
        raise SystemExit(2)

    write_csv(a.out / "nors_poultry_serotype_year.csv", poultry,
              ["year", "cat", "sero", "nb", "ill", "hosp", "dth"])
    write_csv(a.out / "nors_salmonella_attribution.csv", attribution,
              ["cat", "nb", "ill", "hosp", "dth"])
    (a.out / "FETCH_INFO.json").write_text(json.dumps({
        "source": "https://data.cdc.gov/dataset/NORS/5xkq-dg7x",
        "api": BASE,
        "years": [a.y0, a.y1],
        "filter": where,
        "poultry_rows": len(poultry),
        "attribution_rows": len(attribution),
    }, indent=1))
    print(f"wrote {len(poultry)} poultry rows, {len(attribution)} attribution rows "
          f"to {a.out}")


if __name__ == "__main__":
    main()
