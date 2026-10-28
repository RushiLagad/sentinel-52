import { useMemo, useState } from "react";
import SyntheticBadge from "./SyntheticBadge.jsx";
import ConfirmHighConsequence from "./ConfirmHighConsequence.jsx";
import { fmtLbs, fmt3, actionLabel, classLabel } from "../lib/format.js";

// R4. One recommended action per lot, the one-sentence reason, what it costs,
// the opposite action with its cost, and — for hold and divert — a blocking
// confirmation that names the evidence that would reverse it.
export default function RecommendedActionPanel({ actions, picked }) {
  const [filter, setFilter] = useState("high_consequence");
  const [sel, setSel] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const [acks, setAcks] = useState(() => new Set());
  const lots = useMemo(() => {
    let r = actions.lots;
    if (picked) { const [id, cls] = picked.split("|"); r = r.filter((l) => String(l.establishment_id) === id && l.product_class === cls); }
    if (filter === "high_consequence") r = r.filter((l) => l.high_consequence);
    else if (filter !== "all") r = r.filter((l) => l.action === filter);
    return [...r].sort((a, b) => (b.high_consequence - a.high_consequence) || (b.projection ?? 0) - (a.projection ?? 0));
  }, [actions, filter, picked]);
  const lot = lots.find((l) => l.lot_id === sel) || lots[0];
  const counts = useMemo(() => actions.lots.reduce((m, l) => (m[l.action] = (m[l.action] || 0) + 1, m), {}), [actions]);
  return (
    <section className="panel" id="actions">
      <h2>Recommended actions <SyntheticBadge /></h2>
      <p className="lede">{actions.lots.length} simulated lots under the <b>{actions.meta.default_scenario}</b> scenario: {Object.entries(counts).map(([k, v]) => `${v} ${k.replace(/_/g, " ")}`).join(" · ")}. {picked ? <>Showing lots from the plant selected under Current risk. </> : null}Nothing here is executed by this tool.</p>
      <div className="controls">
        <label>Show <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="high_consequence">high-consequence only</option><option value="all">all</option>
          {Object.keys(actionLabel).map((a) => <option key={a} value={a}>{actionLabel[a]}</option>)}
        </select></label>
        <span className="muted small">{lots.length} lots</span>
      </div>
      <div className="grid two">
        <div className="table-wrap" style={{ maxHeight: 440 }}>
          <table>
            <thead><tr><th>Lot</th><th>Plant / product</th><th>Action</th><th className="num">score</th><th className="num">lb</th></tr></thead>
            <tbody>
              {lots.slice(0, 400).map((l) => (
                <tr key={l.lot_id} className={"clickable" + (lot?.lot_id === l.lot_id ? " selected" : "")} onClick={() => setSel(l.lot_id)}>
                  <td className="mono small">{l.lot_id}{acks.has(l.lot_id) ? <span className="badge cat" style={{ marginLeft: 4 }}>read</span> : null}</td>
                  <td className="small">{l.establishment_name}<div className="muted">{classLabel(l.product_class)}</div></td>
                  <td><span className={`badge action-${l.action}`}>{l.action.replace(/_/g, " ")}</span></td>
                  <td className="num">{fmt3(l.projection)}</td>
                  <td className="num">{Math.round(l.pounds).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {lot && (
          <div className="card">
            <h3 style={{ marginTop: 0 }}>{actionLabel[lot.action]} {lot.high_consequence && <span className="badge hc">HIGH-CONSEQUENCE</span>}</h3>
            <p className="ink2"><code>{lot.lot_id}</code> · {lot.establishment_name} <code className="muted">#{lot.establishment_id}</code> · {classLabel(lot.product_class)}</p>
            <dl className="kv">
              <dt>Because</dt><dd>{lot.driver}</dd>
              <dt>Costs</dt><dd>{fmtLbs(lot.pounds)} <SyntheticBadge /> for {lot.dest_county} ({lot.svi_quartile}); {lot.days_left} days of shelf life left</dd>
              <dt>Evidence</dt><dd>FSIS Cat {lot.category ?? "NA"} · 52-wk {lot.pos52 ?? "—"} positives of {lot.n52 ?? "—"} · score {fmt3(lot.projection)}{lot.score_age_days != null ? ` (${lot.score_age_days} days old)` : ""}{lot.scored === false ? " · no recent sampling" : ""}</dd>
              <dt>The other choice</dt><dd>{actionLabel[lot.alternative_action]} — {lot.high_consequence ? `keeps ${fmtLbs(lot.pounds)} in direct distribution and accepts the signal above` : `withholds ${fmtLbs(lot.pounds)} from ${lot.dest_county} on a signal the policy judged too weak`} <SyntheticBadge /></dd>
              {lot.high_consequence && <><dt>Would reverse it</dt><dd>{lot.reversal_evidence}</dd></>}
              {lot.discarded && <><dt>Under this policy</dt><dd>lost — {lot.discard_reason}</dd></>}
            </dl>
            {lot.high_consequence
              ? <button className="danger" style={{ marginTop: "0.6rem" }} onClick={() => setConfirming(lot)}>Review and acknowledge</button>
              : <p className="small muted">Not high-consequence. No confirmation step; nothing is executed either way.</p>}
          </div>
        )}
      </div>
      <ConfirmHighConsequence lot={confirming} onClose={() => setConfirming(null)} onAcknowledge={(id) => setAcks((s) => new Set(s).add(id))} />
    </section>
  );
}
