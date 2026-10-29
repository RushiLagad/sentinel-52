import { useMemo, useState } from "react";
import Frontier from "./charts/Frontier.jsx";
import SyntheticBadge from "./SyntheticBadge.jsx";
import { fmtInt, fmtLbs, fmt3 } from "../lib/format.js";

// R3. The app computes nothing: every point on the frontier and every scenario
// row was produced by 16_decision_layer.py. The threshold slider snaps to the
// precomputed sweep. Review capacity and the food-security weight are varied
// through the named scenarios, which is where they were precomputed; that is
// stated on screen rather than hidden behind a control that pretends to be live.
export default function ScenarioBuilder({ scenarios, equity, selected, onSelect }) {
  const pts = scenarios.frontier;
  const [fi, setFi] = useState(Math.max(0, pts.findIndex((p) => p.hold_at >= 0.1)));
  const p = pts[fi];
  const dominatedBy = useMemo(() => Object.fromEntries((scenarios.dominated || []).map((d) => [d.dominated, d])), [scenarios]);
  const q4 = (name) => equity.quartiles.find((r) => r.scenario === name && /Q4/.test(r.svi_quartile));
  return (
    <section className="panel" id="scenarios">
      <h2>Scenarios and the trade-off <SyntheticBadge /></h2>
      <p className="lede">Four named policies on the same {fmtInt(scenarios.scenarios[0].lots)} simulated lots, and the frontier between the two error types in shared units. {scenarios.frontier_note}</p>

      <h3>Hold threshold</h3>
      <div className="controls">
        <label>hold at <input type="range" min={0} max={pts.length - 1} step={1} value={fi} onChange={(e) => setFi(Number(e.target.value))} /> <b className="mono">{p.hold_at}</b> (divert at {p.divert_at})</label>
        <span className="small muted">{scenarios.controls?.find((c) => c.id === "hold_at")?.note}</span>
      </div>
      <div className="grid three">
        <div className="card stat"><span className="v">{fmt3(p.recall)}</span><span className="k">recall</span></div>
        <div className="card stat"><span className="v">{fmt3(p.precision)}</span><span className="k">precision</span></div>
        <div className="card stat"><span className="v">{fmtLbs(p.pounds_distributed)}</span><span className="k">distributed <SyntheticBadge /></span></div>
        <div className="card stat"><span className="v">{fmtInt(p.avoidable_loss_meals)}</span><span className="k">meals destroyed from plants that did not deteriorate <SyntheticBadge /></span></div>
        <div className="card stat"><span className="v">{fmtInt(p.exposure_meals)}</span><span className="k">meals distributed uncooked from plants that did <SyntheticBadge /></span></div>
        <div className="card stat"><span className="v">{fmtLbs(p.pounds_discarded)}</span><span className="k">discarded <SyntheticBadge /></span></div>
      </div>
      <Frontier points={pts} selectedIndex={fi} onSelect={setFi} />
      <p className="small muted">The curve is not convex: loss falls and then rises as the threshold climbs, because raising the divert threshold pushes lots back into holds, where shelf life kills them. There is no clean optimum, and which point to stand on is a judgement about whose risk counts.</p>

      <h3>Named scenarios. Review capacity and the food-security weight live here</h3>
      <div className="grid two">
        {scenarios.scenarios.map((s) => {
          const e = q4(s.scenario);
          const dom = dominatedBy[s.scenario];
          return (
            <div key={s.scenario} className={"card" + (selected === s.scenario ? " selected" : "")} onClick={() => onSelect(s.scenario)} style={{ cursor: "pointer" }}>
              <b>{s.label}</b>
              {dom && <div className="notice small"><b>Dominated</b> by {dom.by}: {dom.why}. Not a trade-off, just worse.</div>}
              <dl className="kv small" style={{ marginTop: "0.4rem" }}>
                <dt>thresholds</dt><dd>{s.hold_at == null ? "FSIS category rule" : `hold ≥ ${s.hold_at}, divert ≥ ${s.divert_at}`}</dd>
                <dt>review capacity</dt><dd>{s.review_capacity_per_week == null ? "unlimited" : `${s.review_capacity_per_week} / week`} · needs <b>{s.holds_per_week_required?.toFixed(1)}</b> / week{s.review_capacity_exceeded_by > 1 ? <span className="badge hc" style={{ marginLeft: 6 }}>NOT EXECUTABLE</span> : null}</dd>
                <dt>food-security weight</dt><dd>{s.food_security_weight}</dd>
                <dt>precision / recall</dt><dd>{fmt3(s.precision)} / {fmt3(s.recall)}</dd>
                <dt>actions</dt><dd>{s.n_distribute_now} distribute · {s.n_prioritize} prioritize · {s.n_hold_for_review} hold · {s.n_divert} divert</dd>
                <dt>distributed</dt><dd>{fmtLbs(s.pounds_distributed)} <SyntheticBadge /></dd>
                <dt>destroyed, from plants that did not deteriorate</dt><dd><b>{fmtInt(s.avoidable_loss_meals)}</b> meals <SyntheticBadge /></dd>
                <dt>uncooked, from plants that did</dt><dd>{fmtInt(s.exposure_meals)} meals <SyntheticBadge /></dd>
                <dt>share reaching most-vulnerable quartile</dt><dd>{e ? `${e.share_of_all_distribution_pct}%` : "n/a"} <SyntheticBadge /></dd>
              </dl>
            </div>
          );
        })}
      </div>
      <p className="small muted">{scenarios.meta.threshold_caveat}</p>
    </section>
  );
}
