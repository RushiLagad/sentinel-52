import SyntheticBadge from "./SyntheticBadge.jsx";
import { fmtInt, fmtLbs } from "../lib/format.js";

// R6. Whether the policy quietly takes food away from the communities least
// able to replace it. The disparity is stated whichever way it comes out, and
// nothing here optimises it away. The human chooses.
export default function EquityView({ equity, selected }) {
  const rows = equity.quartiles.filter((r) => r.scenario === selected);
  const d = equity.disparity.find((x) => x.scenario === selected);
  const against = d && d.difference_pct_points > 1;
  return (
    <section className="panel" id="equity">
      <h2>Food security and equity <SyntheticBadge /></h2>
      <p className="lede">Destination counties by CDC/ATSDR SVI quartile, for the scenario selected above (<b>{selected}</b>).</p>
      {d && (
        <div className={against ? "notice" : "finding"}>
          <b>Disparity check:</b> withheld share is <b>{d.withheld_pct_most_vulnerable}%</b> in the most vulnerable quartile against <b>{d.withheld_pct_least_vulnerable}%</b> in the least — a difference of <b>{d.difference_pct_points > 0 ? "+" : ""}{d.difference_pct_points} points</b>. {d.direction}.
          {against && <> This policy reduces supply to high-need counties more than to others. That is shown here on the scenario screen, not in a footnote, and it is not corrected automatically.</>}
        </div>
      )}
      <div className="table-wrap" style={{ maxHeight: 300 }}>
        <table>
          <thead><tr><th>SVI quartile</th><th className="num">lots</th><th className="num">offered</th><th className="num">distributed</th><th className="num">withheld</th><th className="num">withheld %</th><th className="num">share of all distribution</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.svi_quartile}>
                <td>{r.svi_quartile}</td><td className="num">{fmtInt(r.lots)}</td>
                <td className="num">{fmtLbs(r.pounds_offered)}</td><td className="num">{fmtLbs(r.pounds_distributed)}</td>
                <td className="num">{fmtLbs(r.pounds_withheld)}</td><td className="num"><b>{r.withheld_pct}%</b></td><td className="num">{r.share_of_all_distribution_pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="small muted">{equity.note}</p>
    </section>
  );
}
