#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26. The endpoint,
# schema and establishment-mark extraction below were validated against the live
# API before this was written. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Fetch FSIS recalls and public health alerts.

Required by the brief under USDA FSIS public data, and distinct from the sampling
data: a recall is a fact about product already in commerce, not a prediction. In
the decision layer a recall affecting held stock outranks any model score.

Endpoint: https://www.fsis.usda.gov/fsis/api/recall/v/1
No key, no registration. Returns the full set as one JSON array (about 2,000
records, roughly 13 MB).

The join problem
----------------
`field_establishment` holds **company names**, not establishment numbers, so it
does not join to our panel. Establishment numbers appear instead inside the
product text, as USDA marks of inspection: "EST. P-50784", "EST. 18004",
"Est. 45640", "EST. P 20935A". This script extracts and normalises them.

Measured on the live data: of 563 poultry-or-Salmonella recalls from 2014 on,
**206 (36.6 percent) carry a recoverable establishment mark**. The rest cannot be
tied to a plant from this feed. That is a real limitation of the recall layer and
belongs in PROVENANCE.md and the report, not buried.

Usage:
  python scripts/12_fetch_fsis_recalls.py --out data/fsis_recalls
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://www.fsis.usda.gov/fsis/api/recall/v/1"

# USDA mark of inspection inside product text. Prefix P (poultry), M (meat),
# V (egg), sometimes absent; number 2 to 5 digits, optional trailing letter.
EST_RE = re.compile(r"\bEST\.?\s*((?:P|M|V)?[-\s]?\d{2,5}[A-Z]?)\b", re.IGNORECASE)
POULTRY_RE = re.compile(r"chicken|turkey|poultry|duck|cornish", re.IGNORECASE)
SALM_RE = re.compile(r"salmonella", re.IGNORECASE)


def flat(v) -> str:
    if isinstance(v, list):
        v = "; ".join(str(x) for x in v)
    return html.unescape(str(v if v is not None else "")).replace("\xa0", " ").strip()


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def est_marks(rec: dict) -> str:
    """Pipe-joined, normalised establishment marks found in the product text."""
    blob = " ".join(flat(rec.get(k)) for k in
                    ("field_product_items", "field_summary", "field_labels", "field_title"))
    found = {m.group(1).replace(" ", "").replace("-", "").upper() for m in EST_RE.finditer(blob)}
    return "|".join(sorted(found))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--from-year", type=int, default=2014, help="match the FSIS sampling panel")
    ap.add_argument("--timeout", type=int, default=120)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    try:
        req = urllib.request.Request(API, headers={"Accept": "application/json",
                                                   "User-Agent": "sentinel-52/1.0 (NAFSI student data challenge)"})
        with urllib.request.urlopen(req, timeout=a.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as exc:  # noqa: BLE001
        print(f"FSIS recall API fetch failed: {exc}", file=sys.stderr)
        print("If this machine cannot reach fsis.usda.gov, the cached CSV in this "
              "directory lets the rest of the pipeline run.", file=sys.stderr)
        raise SystemExit(2)

    rows = []
    for rec in data:
        title = squash(flat(rec.get("field_title")))
        summary = flat(rec.get("field_summary"))
        reason = squash(flat(rec.get("field_recall_reason")))
        year = pd.to_numeric(flat(rec.get("field_year")), errors="coerce")
        rows.append({
            "recall_number": squash(flat(rec.get("field_recall_number"))),
            "recall_date": squash(flat(rec.get("field_recall_date")))[:10],
            "year": year,
            "risk_level": squash(flat(rec.get("field_risk_level"))),
            "recall_class": squash(flat(rec.get("field_recall_classification"))),
            "recall_type": squash(flat(rec.get("field_recall_type"))),
            "reason": reason,
            "outbreak_related": squash(flat(rec.get("field_related_to_outbreak"))),
            "active_notice": squash(flat(rec.get("field_active_notice"))),
            "company": squash(flat(rec.get("field_establishment")))[:80],
            "est_marks": est_marks(rec),
            "n_states": len(rec.get("field_states") or []),
            "states": squash(flat(rec.get("field_states")))[:200],
            "is_poultry_title": bool(POULTRY_RE.search(title)),
            "is_salmonella": bool(SALM_RE.search(reason + " " + title + " " + summary)),
            "title": title[:200],
            "url": squash(flat(rec.get("field_recall_url"))),
        })

    D = pd.DataFrame(rows).drop_duplicates(subset=["recall_number", "recall_date", "title"])
    D = D[D["year"] >= a.from_year]
    rel = D[D["is_poultry_title"] | D["is_salmonella"]].copy()

    D.to_csv(a.out / "fsis_recalls_all.csv", index=False)
    rel.to_csv(a.out / "fsis_recalls_poultry_salmonella.csv", index=False)

    with_mark = int((rel["est_marks"] != "").sum())
    info = {
        "source": API,
        "licence": "US federal government public domain; no key or registration required",
        "records_returned": len(data),
        "after_dedupe_and_year_filter": int(len(D)),
        "from_year": a.from_year,
        "poultry_or_salmonella": int(len(rel)),
        "poultry_title_only": int(rel["is_poultry_title"].sum()),
        "salmonella_mentioned": int(rel["is_salmonella"].sum()),
        "with_recoverable_establishment_mark": with_mark,
        "establishment_mark_recovery_pct": round(100 * with_mark / max(len(rel), 1), 1),
        "outbreak_related_true": int((rel["outbreak_related"].str.lower() == "true").sum()),
        "limitation": ("field_establishment holds company names, not establishment numbers. "
                       "Numbers are recovered from USDA marks in the product text and are "
                       "absent for most records, so recall-to-plant linkage is partial."),
    }
    (a.out / "FETCH_INFO.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
