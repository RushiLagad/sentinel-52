export const fmtInt = (n) => (n == null ? "n/a" : Math.round(n).toLocaleString("en-US"));
export const fmtLbs = (n) => (n == null ? "n/a" : `${Math.round(n).toLocaleString("en-US")} lb`);
export const fmtPct = (x, d = 1) => (x == null ? "n/a" : `${(100 * x).toFixed(d)}%`);
export const fmtPctRaw = (x, d = 1) => (x == null ? "n/a" : `${Number(x).toFixed(d)}%`);
export const fmt3 = (x) => (x == null ? "n/a" : Number(x).toFixed(3));
export const fmt2 = (x) => (x == null ? "n/a" : Number(x).toFixed(2));
export const actionLabel = {
  distribute_now: "Distribute now",
  prioritize: "Prioritize for immediate distribution",
  hold_for_review: "Hold for review",
  divert: "Divert to cooked-meal channel",
};
export const classLabel = (c) => (c || "").replace(/_/g, " ");

// Scenario ids are keys in 16_decision_layer.py; people read these.
export const SCENARIO_LABEL = { rule_based_category: "Rule-based (status quo)", conservative: "Conservative", capacity_matched: "Capacity-matched", food_security_weighted: "Food-security weighted" };
export const scenarioLabel = (id) => SCENARIO_LABEL[id] || id;
