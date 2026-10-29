import { useMemo, useState } from "react";
import SyntheticBadge from "./SyntheticBadge.jsx";
import ConfirmHighConsequence from "./ConfirmHighConsequence.jsx";
import { fmtLbs, fmt3, fmtPct, actionLabel, classLabel } from "../lib/format.js";

// The landing view, and the reason the app exists. A pallet is in front of you;
// here is the call, why, what it costs, what the other choice costs, and what
// would change it. Act, and the next one comes up. The tables further down are
// the evidence behind this screen, not the screen itself.
//
// "Live" here means the interface answers instantly from precomputed results.
// Nothing is scored on the fly, by design: every number was produced by the
// pipeline, carries a source hash, and was reproduced on two machines. A model
// re-run in the browser could not say that.
const ORDER = { divert: 0, hold_for_review: 1, prioritize: 2, distribute_now: 3 };
const VERB = { distribute_now: "Distribute now", prioritize: "Move it first", hold_for_review: "Hold it", divert: "Send it to the cooked-meal channel" };

export default function ReceivingDesk({ actions, risk, names }) {
  const lots = useMemo(() => [...actions.lots].sort((a, b) =>
    (ORDER[a.action] - ORDER[b.action]) || (b.projection ?? 0) - (a.projection ?? 0) || b.pounds - a.pounds), [actions]);
  const [i, setI] = useState(0);
  const [acks, setAcks] = useState(() => new Set());
  const [confirming, setConfirming] = useState(false);
  const [q, setQ] = useState("");
  const lot = lots[i];
  const unit = useMemo(() => risk.units.find((u) => u.establishment_id === lot?.establishment_id && u.product_class === lot?.product_class), [risk, lot]);
  const pending = lots.filter((l) => l.high_consequence && !acks.has(l.lot_id)).length;
  const matches = q ? lots.filter((l) => l.lot_id.toLowerCase().includes(q.toLowerCase()) || (l.establishment_name || "").toLowerCase().includes(q.toLowerCase())).slice(0, 8) : [];
  const next = () => { const j = lots.findIndex((l, k) => k > i && l.high_consequence && !acks.has(l.lot_id)); setI(j >= 0 ? j : Math.min(i + 1, lots.length - 1)); };
  if (!lot) return null;
  // The lot carries the plant's 52-week counts as of the score it was given; the
  // current-risk unit carries them as of the latest window. When the plant has
  // dropped out of the latest window the lot's own counts still stand.
  const ratePct = unit ? fmtPct(unit.observed_rate_52w) : (lot.n52 ? fmtPct(lot.pos52 / lot.n52) : "n/a");
  return (
    <section className="panel desk" id="desk">
      <div className="desk-head">
        <div>
          <h2>Receiving desk</h2>
          <p className="lede">{pending} of {lots.filter((l) => l.high_consequence).length} lots still need a human decision · {acks.size} reviewed this session · scenario <b>{actions.meta.default_scenario}</b></p>
        </div>
        <div className="desk-find">
          <input type="search" placeholder="lot id or plant" value={q} onChange={(e) => setQ(e.target.value)} aria-label="find a lot" />
          {matches.length > 0 && (
            <ul className="desk-matches">{matches.map((m) => <li key={m.lot_id} onClick={() => { setI(lots.indexOf(m)); setQ(""); }}><code>{m.lot_id}</code> {m.establishment_name} · {classLabel(m.product_class)}</li>)}</ul>
          )}
        </div>
      </div>

      <div className={`decision decision-${lot.action}`}>
        <div className="decision-main">
          <div className="decision-eyebrow">{lot.high_consequence ? <span className="badge hc">HIGH-CONSEQUENCE</span> : <span className="badge cat">routine</span>} <span className="muted small">lot {i + 1} of {lots.length}</span></div>
          <div className="decision-verb">{VERB[lot.action]}</div>
          <div className="decision-why">{lot.driver}</div>
          <div className="decision-lot">
            <code>{lot.lot_id}</code> · <b>{lot.establishment_name}</b> <span className="muted">#{lot.establishment_id}</span> · {classLabel(lot.product_class)} · {fmtLbs(lot.pounds)} <SyntheticBadge /> · {lot.days_left} days of shelf life · for {lot.dest_county} ({lot.svi_quartile})
          </div>
        </div>
        <div className="decision-side">
          <div className="stat"><span className="v">{fmt3(lot.projection)}</span><span className="k">probability this plant enters Category 3 within 3 months{lot.score_age_days != null ? ` · score ${lot.score_age_days}d old` : ""}{lot.scored === false ? " · no recent sampling" : ""}</span></div>
          <div className="stat"><span className="v">Cat {lot.category ?? "NA"}</span><span className="k">FSIS category now</span></div>
          <div className="stat"><span className="v">{lot.pos52 ?? "n/a"} / {lot.n52 ?? "n/a"}</span><span className="k">positives / samples, last 52 weeks ({ratePct})</span></div>
          {unit?.calibration_band
            ? <div className="stat"><span className="v">{fmtPct(unit.calibration_band.observed)}</span><span className="k">of plants scored like this went on to Category 3 (n={unit.calibration_band.n})</span></div>
            : <div className="stat"><span className="v muted">not in the latest window</span><span className="k">this plant and product were not scored in the window ending {risk.meta.window_end}; the figures above are as of the lot's own score</span></div>}
        </div>
      </div>

      <div className="grid two" style={{ marginTop: "0.8rem" }}>
        <div className="card">
          <b>The other choice</b>
          <p>{actionLabel[lot.alternative_action]}. {lot.high_consequence ? <>Keeps {fmtLbs(lot.pounds)} <SyntheticBadge /> in direct distribution to {lot.dest_county} and accepts the signal above.</> : <>Withholds {fmtLbs(lot.pounds)} <SyntheticBadge /> from {lot.dest_county} on a signal the policy judged too weak.</>}</p>
          {lot.discarded && <p className="notice small">Under this policy the lot is lost: {lot.discard_reason}.</p>}
        </div>
        <div className="card">
          <b>What would change this call</b>
          <p>{lot.high_consequence ? lot.reversal_evidence : "Nothing is withheld, so there is nothing to reverse. A later sampling result that lifts the score past the hold threshold would bring the lot back here."}</p>
        </div>
      </div>

      <div className="desk-actions">
        {lot.high_consequence
          ? <button className="danger" onClick={() => setConfirming(true)}>{acks.has(lot.lot_id) ? "Reviewed. Open again" : "Review and acknowledge"}</button>
          : <button className="primary" onClick={next}>Noted, next lot</button>}
        <button className="ghost" onClick={() => setI(Math.max(0, i - 1))} disabled={i === 0}>Previous</button>
        <button className="ghost" onClick={() => setI(Math.min(lots.length - 1, i + 1))} disabled={i === lots.length - 1}>Next</button>
        <button className="ghost" onClick={next}>Next needing a decision</button>
        <span className="small muted">Nothing here moves a pallet. Acknowledging records that a person read the call.</span>
      </div>

      <ConfirmHighConsequence lot={confirming ? lot : null} onClose={() => setConfirming(false)} onAcknowledge={(id) => { setAcks((s) => new Set(s).add(id)); setTimeout(next, 0); }} />
    </section>
  );
}
