import Reliability from "./charts/Reliability.jsx";
import { fmt3, fmtPct } from "../lib/format.js";

// R5. What the recommendation rests on and how firm it is: model metrics with
// establishment-clustered bootstrap intervals, calibration, scorer selection,
// burden with the single-outbreak flag, sources by file and hash, and the FSIS
// restriction stated in full.
export default function EvidencePanel({ evidence, burden, meta }) {
  const m = evidence.model, c = evidence.calibration, ci = m.bootstrap_ci;
  const rng = (k) => ci?.[k] ? `${fmt3(ci[k].median)} (${fmt3(ci[k].lo)}–${fmt3(ci[k].hi)})` : "n/a";
  return (
    <section className="panel" id="evidence">
      <h2>Evidence and uncertainty</h2>
      <p className="lede">Horizon {evidence.meta.horizon_months} months. Scorer <code>{c.scorer}</code>, chosen because {c.selection?.reason}.</p>
      <div className="grid two">
        <div>
          <h3>Model, on the full panel</h3>
          <div className="table-wrap" style={{ maxHeight: 260 }}>
            <table>
              <thead><tr><th>scorer</th><th className="num">AUROC</th><th className="num">avg precision</th><th className="num">recall @10%</th><th className="num">Brier</th></tr></thead>
              <tbody>{m.metrics.map((r) => <tr key={r.scorer}><td>{r.scorer}</td><td className="num">{fmt3(r.auroc)}</td><td className="num">{fmt3(r.avg_precision)}</td><td className="num">{fmt3(r.recall_top10pct)}</td><td className="num">{r.brier == null ? "n/a" : fmt3(r.brier)}</td></tr>)}</tbody>
            </table>
          </div>
          <dl className="kv small" style={{ marginTop: "0.5rem" }}>
            <dt>AUROC, projection</dt><dd>{rng("auroc_proj")}</dd>
            <dt>AUROC, gradient boosting</dt><dd>{rng("auroc_gb")}</dd>
            <dt>Δ AUROC (gb − projection)</dt><dd>{rng("d_auroc_gb")}</dd>
            <dt>Δ avg precision</dt><dd>{rng("d_ap_gb")}; the integrated model's advantage is not distinguishable from zero</dd>
            <dt>interval</dt><dd>95%, {m.bootstrap_establishments} establishments resampled whole. {m.interval_note}</dd>
            <dt>test set</dt><dd>{m.task?.test_rows?.toLocaleString()} unit-months, {m.task?.test_new_failures} new Category 3 entries, base rate {m.task?.test_positive_pct}%</dd>
            <dt>Category 2 flag</dt><dd>recall {fmt3(m.cat2_flag?.recall)}, precision {fmt3(m.cat2_flag?.precision)}, flags {m.cat2_flag?.flagged_pct}% of units</dd>
          </dl>
        </div>
        <div>
          <h3>Calibration: are the scores believable numbers</h3>
          <Reliability bins={c.reliability} />
          <p className="small ink2">ECE {c.ece} · Brier {c.brier}. Of units in the top decile, predicted {fmtPct(c.reliability.at(-1)?.mean_pred)} against observed {fmtPct(c.reliability.at(-1)?.observed)}. Gradient boosting at this horizon: ECE {c.all_scorers?.gb?.ece}, which is why it is not the scorer here.</p>
        </div>
      </div>

      <h3>Illness burden by serotype, joined at serotype and year, never establishment</h3>
      {burden.serotypes?.length ? (
        <div className="table-wrap" style={{ maxHeight: 300 }}>
          <table>
            <thead><tr><th>serotype</th><th className="num">outbreaks</th><th className="num">illnesses</th><th className="num">hospitalisations</th><th className="num">from a single outbreak</th><th>in FSIS KPI</th></tr></thead>
            <tbody>{burden.serotypes.map((s) => (
              <tr key={s.serotype}><td>{s.serotype}</td><td className="num">{s.outbreaks}</td><td className="num">{s.illnesses}</td><td className="num">{s.hospitalizations}</td>
                <td className="num">{s.pct_hosp_from_largest_row}%{s.pct_hosp_from_largest_row >= 80 ? <span className="badge hc" style={{ marginLeft: 6 }}>RESTS ON ONE EVENT</span> : null}</td>
                <td>{s.in_fsis_kpi ? "yes" : "no"}</td></tr>
            ))}</tbody>
          </table>
        </div>
      ) : <p className="muted small">Burden table not in this build. Run <code>10_burden_weighting.py</code> then <code>17_build_app_data.py</code>.</p>}
      <p className="small muted">{burden.note}</p>

      <h3>Resistance by serotype, FSIS WGS calls</h3>
      <div className="table-wrap" style={{ maxHeight: 260 }}>
        <table>
          <thead><tr><th>species</th><th>serotype</th><th className="num">isolates</th><th className="num">≥3 classes</th><th className="num">ceftriaxone</th><th className="num">quinolone</th><th className="num">no resistance</th></tr></thead>
          <tbody>{burden.resistance_by_serotype.map((r, i) => <tr key={i}><td>{r.species}</td><td>{r.serotype_clean}</td><td className="num">{r.isolates}</td><td className="num"><b>{r.mdr3_pct}%</b></td><td className="num">{r.ceftriaxone_r_pct}%</td><td className="num">{r.quinolone_r_pct}%</td><td className="num">{r.no_resistance_pct}%</td></tr>)}</tbody>
        </table>
      </div>

      <h3>Where every number comes from</h3>
      <ul className="sources">{(evidence.sources || meta.sources || []).map((s) => <li key={s.file}><code>{s.file}</code> <span className="muted">sha256 {s.sha256_8} · {s.modified_utc}</span></li>)}</ul>
      <ul className="sources">{(evidence.documentation || []).map((d, i) => <li key={i}>{typeof d === "string" ? <code>{d}</code> : <a href={d.url || "#"}>{d.title || d.file}</a>}</li>)}</ul>
      {(evidence.restrictions || meta.restrictions || []).map((r, i) => <p key={i} className="restriction">{r}</p>)}
    </section>
  );
}
