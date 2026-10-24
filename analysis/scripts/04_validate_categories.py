#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and run end to
# end on the real FSIS files. Review it before relying on it.
# -----------------------------------------------------------------------------
"""Check that categories rebuilt from sample data match what FSIS posted.

Each file in --posted-dir is one FSIS monthly posting (establishment number,
product class, category) saved as CSV with its window text.

Usage:
  python scripts/04_validate_categories.py --data data/processed --posted-dir data/validation --out outputs
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from fsis_categories import POSTED_NAME, window_counts


def window_end_from_text(text: str) -> pd.Timestamp:
    m = re.search(r"through\s+(.+)$", text.strip())
    return pd.Timestamp(m.group(1)).normalize()


def p_token(num: pd.Series) -> pd.Series:
    """Poultry grant number inside an establishment number such as 'M112+P112+V112'."""
    return num.astype("string").str.extract(r"(?:^|\+)(P[0-9A-Z]+)", expand=False)


def compare(S: pd.DataFrame, posted: pd.DataFrame, end, rule: str, result_col) -> tuple[dict, pd.DataFrame]:
    mine = window_counts(S, end, rule=rule, result_col=result_col)
    # Establishment numbers in the sample files are current ones; older postings may show an earlier form
    # of the same number. Where the full number does not match, fall back to the poultry grant number.
    posted = posted.copy(); mine = mine.copy()
    exact = set(zip(mine["establishment_number"], mine["product_class"]))
    need = ~pd.Series(list(zip(posted["establishment_number"], posted["product_class"])), index=posted.index).isin(exact)
    mine["ptok"] = p_token(mine["establishment_number"]); lut = mine.dropna(subset=["ptok"]).drop_duplicates(["ptok", "product_class"], keep=False).set_index(["ptok", "product_class"])["establishment_number"]
    keys = list(zip(p_token(posted.loc[need, "establishment_number"]), posted.loc[need, "product_class"]))
    posted.loc[need, "establishment_number"] = [lut.get(k, orig) for k, orig in zip(keys, posted.loc[need, "establishment_number"])]
    mine = mine.drop(columns="ptok")
    m = posted.merge(mine, on=["establishment_number", "product_class"], how="outer", suffixes=("_posted", "_rebuilt"), indicator=True)
    both = m[m["_merge"] == "both"].copy(); both["match"] = both["category_posted"] == both["category_rebuilt"]
    rated = both[both["category_posted"] != "NA"]
    res = {"posted_rows": int(len(posted)), "joined": int(len(both)), "posted_only": int((m["_merge"] == "left_only").sum()),
           "rebuilt_only": int((m["_merge"] == "right_only").sum()), "match": int(both["match"].sum()),
           "match_pct": round(100 * float(both["match"].mean()), 2), "rated_rows": int(len(rated)),
           "rated_match_pct": round(100 * float(rated["match"].mean()), 2),
           "posted_cat3": int((both["category_posted"] == "3").sum()),
           "posted_cat3_rebuilt_cat3": int(((both["category_posted"] == "3") & (both["category_rebuilt"] == "3")).sum()),
           "rebuilt_cat3_not_posted_cat3": int(((both["category_posted"] != "3") & (both["category_rebuilt"] == "3")).sum())}
    return res, both


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True); ap.add_argument("--posted-dir", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    S = pd.read_parquet(a.data / "samples.parquet")
    out = {}
    for f in sorted(a.posted_dir.glob("posted_categories_*.csv")):
        posted = pd.read_csv(f, dtype=str, keep_default_na=False)
        posted["product_class"] = posted["product_class_posted"].str.strip().map(POSTED_NAME)
        posted["category"] = posted["category"].str.strip().replace({"": "NA"})
        end = window_end_from_text(posted["window_text"].iloc[0])
        key = str(end.date()); out[key] = {"file": f.name, "window_text": posted["window_text"].iloc[0]}
        for label, rule, col in [("percent_rule_all_positives", "percent", "sal_result"), ("posted_rule_all_positives", "fsis_posted", "sal_result"),
                                 ("posted_rule_excl_vaccine", "fsis_posted", "sal_result_cat"), ("final_rule", "fsis_posted", None)]:
            res, both = compare(S, posted[["establishment_number", "product_class", "category"]], end, rule, col)
            out[key][label] = res
        xt = pd.crosstab(both["category_posted"], both["category_rebuilt"])
        out[key]["crosstab_final"] = {str(k): {str(c): int(v) for c, v in row.items()} for k, row in xt.iterrows()}
        both[~both["match"]][["establishment_number", "product_class", "category_posted", "category_rebuilt", "n", "pos"]].to_csv(a.out / f"category_mismatches_{key}.csv", index=False)
        r = out[key]
        print(f"\nwindow ending {key}  ({f.name}): posted rows {r['final_rule']['posted_rows']}, joined {r['final_rule']['joined']}, "
              f"posted-only {r['final_rule']['posted_only']}")
        for label in ("percent_rule_all_positives", "posted_rule_all_positives", "posted_rule_excl_vaccine", "final_rule"):
            print(f"   {label:28s} match {r[label]['match_pct']:6.2f}%   (rated 1/2/3 rows: {r[label]['rated_match_pct']:6.2f}%)   "
                  f"Cat 3 recovered {r[label]['posted_cat3_rebuilt_cat3']}/{r[label]['posted_cat3']}, extra Cat 3 {r[label]['rebuilt_cat3_not_posted_cat3']}")
        print(xt.to_string())
    (a.out / "category_validation.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    main()
