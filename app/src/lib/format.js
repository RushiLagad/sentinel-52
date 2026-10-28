export const fmtInt = (n) => (n == null ? "—" : Math.round(n).toLocaleString("en-US"));
export const fmtLbs = (n) => (n == null ? "—" : `${Math.round(n).toLocaleString("en-US")} lb`);
export const fmtPct = (x, d = 1) => (x == null ? "—" : `${(100 * x).toFixed(d)}%`);
export const fmtPctRaw = (x, d = 1) => (x == null ? "—" : `${Number(x).toFixed(d)}%`);
export const fmt3 = (x) => (x == null ? "—" : Number(x).toFixed(3));
export const fmt2 = (x) => (x == null ? "—" : Number(x).toFixed(2));
export const actionLabel = {
  distribute_now: "Distribute now",
  prioritize: "Prioritize for immediate distribution",
  hold_for_review: "Hold for review",
  divert: "Divert to cooked-meal channel",
};
export const classLabel = (c) => (c || "").replace(/_/g, " ");
