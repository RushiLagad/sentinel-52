// R2. Recalls and public health alerts FSIS has already published are facts;
// model scores are forecasts. Facts are pinned above forecasts, always.
export default function AlertQueue({ alerts, names }) {
  const groups = [...new Set(alerts.alerts.map((a) => a.rank_group))].sort();
  return (
    <section className="panel" id="alerts">
      <h2>Alert queue</h2>
      <p className="lede">{alerts.alerts.length} items. Published recalls and alerts are pinned above anything the model produces.</p>
      {groups.map((g) => (
        <div key={g}>
          <h3>{g === 0 ? "Published by FSIS" : "From the model"}</h3>
          <div className="table-wrap" style={{ maxHeight: 360 }}>
            <table>
              <thead><tr><th>Date</th><th>What</th><th>Marks / plant</th><th>Where</th><th>Why here</th></tr></thead>
              <tbody>
                {alerts.alerts.filter((a) => a.rank_group === g).map((a, i) => (
                  <tr key={i}>
                    <td className="mono small">{a.date}</td>
                    <td>{a.kind === "recall" ? <span className="badge pin">RECALL</span> : <span className="badge cat">{a.kind}</span>} {a.url ? <a href={a.url} target="_blank" rel="noreferrer">{a.title}</a> : a.title}{a.risk_level ? <div className="small muted">{a.risk_level} · {a.reason}</div> : null}</td>
                    <td className="mono small">{a.establishment_marks || (a.establishment_id != null ? `${names[a.establishment_id] || ""} #${a.establishment_id}` : "—")}</td>
                    <td className="small">{a.states || a.product_class || "—"}</td>
                    <td className="small muted">{a.why_pinned || a.why || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
      <p className="small muted">Establishment marks are recovered from recall text by pattern; FSIS publishes them for only about a third of poultry-or-Salmonella notices, so a plant with no recall here may be unresolvable rather than clear.</p>
    </section>
  );
}
