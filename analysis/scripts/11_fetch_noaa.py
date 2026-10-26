#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-26.
# NOT YET RUN AGAINST THE LIVE API. The container it was written in has no NOAA
# token and no route to ncei.noaa.gov. Expect the first run to need a fix; the
# error messages are written to make that quick. Review before relying on it.
# -----------------------------------------------------------------------------
"""Fetch NOAA/NCEI monthly climate summaries for the states holding poultry establishments.

Required by the brief. Uses Climate Data Online v2 and the GSOM dataset (Global
Summary of the Month), which is already monthly, so we pull roughly three orders
of magnitude less data than daily summaries would need.

Token
-----
Free, from https://www.ncei.noaa.gov/cdo-web/token. Read from the environment
variable NOAA_CDO_TOKEN. It is never written to disk or committed.

    $env:NOAA_CDO_TOKEN = "..."         # PowerShell, current session
    export NOAA_CDO_TOKEN=...           # bash

What this produces
------------------
One row per state per month: mean of TAVG, TMAX and PRCP across a **fixed, small
panel of long-record stations** in that state, plus the station count.

Why a station panel rather than every station
---------------------------------------------
A state-level GSOM query returns every GHCND station in the state, which runs to
tens of thousands of station-months per state. A first version of this script
capped pagination and silently truncated at 60,000 records for the larger states,
which would have produced a biased sample presented as a complete one.

Instead this selects, per state, the N stations with the highest CDO
`datacoverage` whose record spans the whole requested window, ties broken by
station id so the selection is deterministic and reproducible. The chosen
stations are written to `noaa_stations_used.csv` so the panel is auditable.

**This is a station-panel average, not an area-weighted state mean.** Long-record
stations skew toward airports and larger towns. For the use here, a monthly
state-level covariate on a 52-week sampling window, that is adequate, and the
limitation belongs in PROVENANCE.md. It would not support a climatological claim,
and we make none.

Prior expectation, worth stating before the result arrives: the ablation in
`05d_ablation.py` already finds month-of-year within noise for this outcome, so
climate may well add little. The brief requires the source; it does not require
the source to help. Report the marginal value honestly either way.

Usage:
  python scripts/11_fetch_noaa.py --data data/processed --out data/noaa
  python scripts/11_fetch_noaa.py --out data/noaa --states AR GA AL NC MS
  python scripts/11_fetch_noaa.py --out data/noaa --stations-per-state 12
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

API = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"
STATIONS_API = "https://www.ncei.noaa.gov/cdo-web/api/v2/stations"
DATASET = "GSOM"
DATATYPES = ["TAVG", "TMAX", "PRCP"]
PAGE = 1000
# CDO documents 5 requests/second; stay well under it.
SLEEP = 0.25

# The 49 states and territories holding poultry establishments in the FSIS panel,
# as observed in data/processed/samples.parquet on 2026-10-26. Used when that file
# is absent, which it is in a fresh clone because data/processed is gitignored.
PANEL_STATES = [
    "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "GU", "HI", "IA", "ID",
    "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MS", "NC",
    "NE", "NH", "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "PR", "RI", "SC",
    "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY",
]

FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09",
    "DE": "10", "DC": "11", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17",
    "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31",
    "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38",
    "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46",
    "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56", "PR": "72", "GU": "66", "VI": "78",
}


def get(url: str, token: str, timeout: int) -> dict:
    req = urllib.request.Request(url, headers={"token": token, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
    return json.loads(body) if body.strip() else {}


def pick_stations(fips: str, start: str, end: str, token: str, timeout: int,
                  n: int) -> list[dict]:
    """The n best-covered stations in a state whose record spans the whole window.

    Deterministic: sorted by datacoverage descending, then station id ascending.
    """
    cands, offset = [], 1
    while True:
        q = [("datasetid", DATASET), ("locationid", f"FIPS:{fips}"),
             ("startdate", start), ("enddate", end),
             ("limit", str(PAGE)), ("offset", str(offset))]
        url = STATIONS_API + "?" + urllib.parse.urlencode(q)
        j = get(url, token, timeout)
        res = j.get("results", [])
        cands.extend(res)
        total = (j.get("metadata", {}).get("resultset", {}) or {}).get("count", 0)
        offset += PAGE
        if offset > total or not res:
            break
        time.sleep(SLEEP)

    def spans(st: dict) -> bool:
        return (st.get("mindate", "9999") <= start) and (st.get("maxdate", "0000") >= end)

    full = [c for c in cands if spans(c)] or cands          # fall back if none span it
    full.sort(key=lambda c: (-float(c.get("datacoverage") or 0), c.get("id", "")))
    return full[:n]


def fetch_station_data(station_ids: list[str], start: str, end: str, token: str,
                       timeout: int, max_pages: int) -> list[dict]:
    """GSOM records for an explicit, bounded set of stations over one window."""
    out, offset, pages = [], 1, 0
    while pages < max_pages:
        q = [("datasetid", DATASET), ("startdate", start), ("enddate", end),
             ("units", "metric"), ("limit", str(PAGE)), ("offset", str(offset))]
        q += [("datatypeid", d) for d in DATATYPES]
        q += [("stationid", sid) for sid in station_ids]
        url = API + "?" + urllib.parse.urlencode(q)
        try:
            j = get(url, token, timeout)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2.0)
                j = get(url, token, timeout)
            else:
                raise
        res = j.get("results", [])
        out.extend(res)
        pages += 1
        total = (j.get("metadata", {}).get("resultset", {}) or {}).get("count", 0)
        offset += PAGE
        if offset > total or not res:
            break
        time.sleep(SLEEP)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--data", type=Path, default=None,
                    help="data/processed, to read the state list from samples.parquet")
    ap.add_argument("--states", nargs="*", default=None, help="override the state list")
    ap.add_argument("--start", default="2013-10-01", help="FY2014 onward, to match the panel")
    ap.add_argument("--end", default="2026-09-30")
    ap.add_argument("--chunk-years", type=int, default=5, help="CDO limits the date span per call")
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--max-pages", type=int, default=20)
    ap.add_argument("--stations-per-state", type=int, default=8,
                    help="size of the per-state long-record station panel")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("NOAA_CDO_TOKEN", "").strip()
    if not token:
        print("NOAA_CDO_TOKEN is not set in the environment.\n"
              "Get a free token at https://www.ncei.noaa.gov/cdo-web/token, then:\n"
              '  PowerShell:  [Environment]::SetEnvironmentVariable("NOAA_CDO_TOKEN","<token>","User")\n'
              "               (then open a NEW terminal)\n"
              "  bash:        export NOAA_CDO_TOKEN=<token>", file=sys.stderr)
        raise SystemExit(2)

    if a.states:
        states = [s.upper() for s in a.states]
    else:
        panel = (a.data / "samples.parquet") if a.data else None
        if panel and panel.exists():
            S = pd.read_parquet(panel, columns=["establishment_state"])
            states = sorted(S["establishment_state"].dropna().unique())
        else:
            if panel:
                print(f"{panel} not found (data/processed is gitignored and rebuilt by "
                      f"run_all.py); using the recorded panel state list instead.", file=sys.stderr)
            states = list(PANEL_STATES)

    unknown = [s for s in states if s not in FIPS]
    states = [s for s in states if s in FIPS]
    if unknown:
        print(f"skipping states with no FIPS mapping: {unknown}", file=sys.stderr)

    # date windows, because CDO rejects spans longer than about ten years
    windows, cur = [], pd.Timestamp(a.start)
    endts = pd.Timestamp(a.end)
    while cur < endts:
        nxt = min(cur + pd.DateOffset(years=a.chunk_years), endts)
        windows.append((cur.date().isoformat(), nxt.date().isoformat()))
        cur = nxt + pd.Timedelta(days=1)

    rows, failures, chosen = [], [], []
    for i, st in enumerate(states, 1):
        try:
            panel = pick_stations(FIPS[st], a.start, a.end, token, a.timeout,
                                  a.stations_per_state)
        except Exception as exc:  # noqa: BLE001
            failures.append({"state": st, "stage": "stations", "error": str(exc)[:200]})
            print(f"  [{i}/{len(states)}] {st}: station lookup failed", flush=True)
            continue
        if not panel:
            failures.append({"state": st, "stage": "stations", "error": "no stations returned"})
            print(f"  [{i}/{len(states)}] {st}: no stations", flush=True)
            continue
        ids = [p["id"] for p in panel]
        for p in panel:
            chosen.append({"state": st, "station": p.get("id"), "name": p.get("name"),
                           "datacoverage": p.get("datacoverage"),
                           "mindate": p.get("mindate"), "maxdate": p.get("maxdate"),
                           "latitude": p.get("latitude"), "longitude": p.get("longitude")})
        got = 0
        for (s0, s1) in windows:
            try:
                recs = fetch_station_data(ids, s0, s1, token, a.timeout, a.max_pages)
            except Exception as exc:  # noqa: BLE001
                failures.append({"state": st, "window": [s0, s1], "stage": "data",
                                 "error": str(exc)[:200]})
                continue
            for r in recs:
                rows.append({"state": st, "date": r.get("date", "")[:7],
                             "datatype": r.get("datatype"), "station": r.get("station"),
                             "value": r.get("value")})
                got += 1
            time.sleep(SLEEP)
        print(f"  [{i}/{len(states)}] {st}: {len(ids)} stations, {got} records", flush=True)

    if not rows:
        print("no records returned; nothing written", file=sys.stderr)
        raise SystemExit(3)

    R = pd.DataFrame(rows)
    R["value"] = pd.to_numeric(R["value"], errors="coerce")
    wide = (R.pivot_table(index=["state", "date"], columns="datatype",
                          values="value", aggfunc="mean").reset_index())
    stations = (R.groupby(["state", "date"])["station"].nunique()
                .rename("n_stations").reset_index())
    M = wide.merge(stations, on=["state", "date"], how="left")
    M["year"] = M["date"].str.slice(0, 4).astype(int)
    M["month"] = M["date"].str.slice(5, 7).astype(int)
    M.to_csv(a.out / "noaa_state_month.csv", index=False)
    pd.DataFrame(chosen).to_csv(a.out / "noaa_stations_used.csv", index=False)

    info = {
        "source": "NOAA NCEI Climate Data Online v2",
        "api": API, "dataset": DATASET, "datatypes": DATATYPES, "units": "metric",
        "licence": "US federal government public domain; free token required",
        "window": [a.start, a.end],
        "states_requested": len(states), "states_with_data": int(M["state"].nunique()),
        "rows": int(len(M)),
        "median_stations_per_state_month": float(M["n_stations"].median()),
        "stations_per_state_requested": a.stations_per_state,
        "stations_selected_total": len(chosen),
        "station_selection": ("highest CDO datacoverage among stations whose record spans the "
                              "whole window, ties broken by station id; deterministic and listed "
                              "in noaa_stations_used.csv"),
        "failures": failures,
        "limitation": ("Station-panel average, not an area-weighted state mean. Long-record "
                       "stations skew toward airports and larger towns. Adequate as a monthly "
                       "state covariate; not adequate for a climatological claim."),
    }
    (a.out / "FETCH_INFO.json").write_text(json.dumps(info, indent=1))
    print(json.dumps({k: info[k] for k in
                      ("states_requested", "states_with_data", "rows",
                       "median_stations_per_state_month")}, indent=1))
    if failures:
        print(f"\n{len(failures)} state-window fetches failed; see FETCH_INFO.json", file=sys.stderr)


if __name__ == "__main__":
    main()
