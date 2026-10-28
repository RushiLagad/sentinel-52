import { useMemo, useState } from "react";
import { fmtPct, fmt3, classLabel } from "../lib/format.js";

// R1. Every plant-and-product unit with its score, the FSIS category it
// currently holds, the observed 52-week rate with an interval, and the
// calibration band it sits in. No name appears next to a burden figure; this
// view carries no illness data at all.
export default function CurrentRiskView({ risk, names, onPick, picked }) {
  const [cls, setCls] = useState("all");
  const [supplierOnly, setSupplierOnly] = useState(true);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState({ k: "score", d: -1 });
  const classes = useMemo(() => [...new Set(risk.units.map((u) => u.product_class))].sort(), [risk]);
  const rows = useMemo(() => {
    let r = risk.units;
    if (cls !== "all") r = r.filter((u) => u.product_class === cls);
    if (supplierOnly) r = r.filter((u) => u.is_supplier);
    if (q) { const s = q.toLowerCase(); r = r.filter((u) => String(u.establishment_id).includes(s) || (names[u.establishment_id] || "").toLowerCase().includes(s)); }
    const cmp = (a, b) => { const x = a[sort.k] ?? -1, y = b[sort.k] ?? -1; return x < y ? -1 : x > y ? 1 : 0; };
    return [...r].sort((a, b) => cmp(a, b) * -sort.d);   // d = -1 means descending
  }, [risk, cls, supplierOnly, q, sort, names]);
  const th = (k, label, num) => (
    <th className={num ? "num" : ""} onClick={() => setSort((s) => ({ k, d: s.k === k ? -s.d : -1 }))} style={{ cursor: "pointer" }}>
      {label}{sort.k === k ? (sort.d < 0 ? " ↓" : " ↑") : ""}
    </th>
  );
  return (
    <section className="panel" id="risk">
      <h2>Current risk</h2>
      <p className="lede">{risk.units.length} plant-and-product units scored at the {risk.meta.horizon_months}-month horizon, window ending {risk.meta.window_end}. Scorer: <code>{risk.meta.scorer}</code>, chosen by measured calibration. {risk.meta.suppliers} units are this food bank's suppliers.</p>
      <div className="controls">
        <label>Product <select value={cls} onChange={(e) => setCls(e.target.value)}><option value="all">all</option>{classes.map((c) => <option key={c} value={c}>{classLabel(c)}</option>)}</select></label>
        <label><input type="checkbox" checked={supplierOnly} onChange={(e) => setSupplierOnly(e.target.checked)} /> suppliers only</label>
        <label>Find <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="plant id or name" /></label>
        <span className="muted small">{rows.length} shown</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr>
            <th>Plant</th><th>Product</th>{th("category", "FSIS category")}{th("score", "Score", true)}{th("observed_rate_52w", "52-wk rate", true)}<th className="num">95% interval</th><th className="num">n / pos</th><th>Calibration band</th>
          </tr></thead>
          <tbody>
            {rows.map((u) => {
              const key = `${u.establishment_id}|${u.product_class}`;
              return (
                <tr key={key} className={"clickable" + (picked === key ? " selected" : "")} onClick={() => onPick(key)}>
                  <td>{names[u.establishment_id] || <span className="muted">plant</span>} <code className="muted">#{u.establishment_id}</code></td>
                  <td>{classLabel(u.product_class)}</td>
                  <td><span className="badge cat">Cat {u.category ?? "NA"}</span></td>
                  <td className="num">{fmt3(u.score)}</td>
                  <td className="num">{fmtPct(u.observed_rate_52w)}</td>
                  <td className="num muted">{fmtPct(u.rate_interval_95?.lo)}–{fmtPct(u.rate_interval_95?.hi)}</td>
                  <td className="num muted">{u.samples_52w} / {u.positives_52w}</td>
                  <td className="small">{u.calibration_band ? <>of units scored like this, <b>{fmtPct(u.calibration_band.observed)}</b> went on to elevated risk (predicted {fmtPct(u.calibration_band.mean_predicted)}, n={u.calibration_band.n})</> : "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="small muted">Interval: {risk.units[0]?.rate_interval_95?.method}. The score is a probability of entering FSIS Category 3 within the horizon; it is not a statement about any product's condition.</p>
    </section>
  );
}
