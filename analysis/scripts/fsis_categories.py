# -----------------------------------------------------------------------------
# AI-ASSISTED CODE: drafted with Claude (Anthropic) on 2026-10-09 and checked
# against FSIS's own posted categories (see 04_validate_categories.py).
# -----------------------------------------------------------------------------
"""Rebuild FSIS Salmonella performance categories from sample-level data.

What FSIS publishes (Directive 10,250.2 and the monthly posting page):
  * window = 52 consecutive Sunday-to-Saturday weeks
  * only routine verification samples count (project codes HC_*), never follow-up
  * Category 1: at or below half of the maximum allowable percent positive
    Category 2: above half, but meeting the maximum
    Category 3: above the maximum
    NA: fewer than the minimum number of samples, and not already over the
        maximum NUMBER of positives the standard allows

What had to be inferred by matching FSIS's posted tables (three windows,
2020, 2023 and 2026; agreement is reported by 04_validate_categories.py):
  * positives typed "Possible Vaccine Strain" are not counted for categorizations
    calculated on or after April 1, 2024 (FSIS Constituent Update, March 1,
    2024). Windows ending before 2024-03-30 count every positive.
  * when a window holds FEWER samples than the standard's sample set (51, 52 or
    56), the allowed number of positives is the standard scaled to the samples
    taken and rounded UP; once the set is full the exact percent applies.
    Example, young chicken carcasses (5 of 51): 3 positives of 50 is Category 1,
    3 of 51 is Category 2.
This rounding rule is empirical. It is not stated in the FSIS documents read so
far, so describe it that way.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# product_class: (max positives, of n samples, minimum samples to assess)
STANDARDS = {
    "chicken_carcass": (5, 51, 11),
    "turkey_carcass": (4, 56, 14),
    "comminuted_chicken": (13, 52, 10),
    "comminuted_turkey": (7, 52, 10),
    "chicken_parts": (8, 52, 10),
}
POSTED_NAME = {
    "Young Chicken Carcasses": "chicken_carcass",
    "Young Turkey Carcasses": "turkey_carcass",
    "Comminuted Chicken": "comminuted_chicken",
    "Comminuted Turkey": "comminuted_turkey",
    "Chicken Parts": "chicken_parts",
}
EPS = 1e-9
# first window end whose categorization FSIS calculated on or after April 1, 2024
VACCINE_EXCLUSION_FROM = pd.Timestamp("2024-03-30")


def window_bounds(end_saturday) -> tuple[pd.Timestamp, pd.Timestamp]:
    """52-week window ending on the given Saturday (inclusive on both ends)."""
    end = pd.Timestamp(end_saturday).normalize()
    if end.dayofweek != 5:
        raise ValueError(f"{end.date()} is not a Saturday")
    return end - pd.Timedelta(days=52 * 7 - 1), end


def last_saturday_of_month(year: int, month: int) -> pd.Timestamp:
    d = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
    return (d - pd.Timedelta(days=(d.dayofweek - 5) % 7)).normalize()


def allowed_positives(n, product_class: str, rule: str = "fsis_posted") -> tuple[np.ndarray, np.ndarray]:
    """(max positives for Category 1, max positives for Category 2) for windows holding n samples."""
    max_pos, of_n, _ = STANDARDS[product_class]
    n = np.asarray(n, dtype=float)
    r3, r1 = max_pos / of_n, max_pos / of_n / 2
    exact1, exact3 = np.floor(n * r1 + EPS), np.floor(n * r3 + EPS)          # same as comparing percents
    if rule == "percent":
        return exact1, exact3
    up1, up3 = np.ceil(n * r1 - EPS), np.ceil(n * r3 - EPS)                    # scaled standard, rounded up
    full = n >= of_n
    return np.where(full, exact1, up1), np.where(full, exact3, up3)


def categorize(n, pos, product_class: str, rule: str = "fsis_posted") -> np.ndarray:
    """Vectorised category assignment. Returns an object array of '1', '2', '3', 'NA'."""
    max_pos, _, min_n = STANDARDS[product_class]
    n = np.asarray(n, dtype=float); pos = np.asarray(pos, dtype=float)
    a1, a3 = allowed_positives(n, product_class, rule)
    cat = np.where(pos > a3, "3", np.where(pos > a1, "2", "1")).astype(object)
    small = n < min_n
    cat[small] = np.where(pos[small] > max_pos, "3", "NA")
    return cat


def window_counts(samples: pd.DataFrame, end_saturday, programs=("routine",), rule: str = "fsis_posted",
                  result_col: str | None = None) -> pd.DataFrame:
    """n, positives and category per establishment and product class inside one 52-week window.

    result_col=None picks the column FSIS would have used for that window: every
    positive before the vaccine-strain exclusion, sal_result_cat after it.
    """
    start, end = window_bounds(end_saturday)
    if result_col is None:
        result_col = "sal_result_cat" if end >= VACCINE_EXCLUSION_FROM else "sal_result"
    d = samples[(samples["collection_date"] >= start) & (samples["collection_date"] <= end)
                & samples["program"].isin(programs) & samples[result_col].notna()
                & samples["product_class"].isin(STANDARDS)]
    g = (d.groupby(["establishment_id", "product_class"], observed=True)
           .agg(n=(result_col, "size"), pos=(result_col, "sum"),
                establishment_number=("establishment_number", "last"), establishment_state=("establishment_state", "last"),
                first_sample=("collection_date", "min"), last_sample=("collection_date", "max"))
           .reset_index())
    g["pos"] = g["pos"].astype(int)
    g["pct"] = 100 * g["pos"] / g["n"]
    g["category"] = "NA"
    for cls in STANDARDS:
        m = g["product_class"] == cls
        if m.any():
            g.loc[m, "category"] = categorize(g.loc[m, "n"].to_numpy(), g.loc[m, "pos"].to_numpy(), cls, rule)
    g["window_start"], g["window_end"] = start, end
    return g
