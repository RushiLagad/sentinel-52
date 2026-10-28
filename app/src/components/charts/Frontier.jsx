// The trade-off frontier (R3.5). Drawn as SVG so it needs no chart library and
// so the palette is exactly the validated one. One axis: the two error types
// share units (meals), which is the whole reason they can be plotted together.
export default function Frontier({ points, selectedIndex, onSelect }) {
  const W = 640, H = 300, m = { t: 18, r: 18, b: 44, l: 64 };
  const xs = points.map((p) => p.exposure_meals), ys = points.map((p) => p.avoidable_loss_meals);
  const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = 0, ymax = Math.max(...ys) * 1.08;
  const sx = (x) => m.l + ((x - xmin) / (xmax - xmin || 1)) * (W - m.l - m.r);
  const sy = (y) => H - m.b - ((y - ymin) / (ymax - ymin || 1)) * (H - m.t - m.b);
  const path = points.map((p, i) => `${i ? "L" : "M"}${sx(p.exposure_meals).toFixed(1)},${sy(p.avoidable_loss_meals).toFixed(1)}`).join(" ");
  const yt = [0, 0.25, 0.5, 0.75, 1].map((f) => ymin + f * (ymax - ymin));
  const xt = [0, 0.5, 1].map((f) => xmin + f * (xmax - xmin));
  const k = (n) => `${Math.round(n / 1000)}k`;
  return (
    <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Frontier: avoidable food loss against exposure, both in meals, across hold thresholds">
      {yt.map((v) => <line key={v} x1={m.l} x2={W - m.r} y1={sy(v)} y2={sy(v)} stroke="var(--line)" strokeWidth="1" />)}
      {yt.map((v) => <text key={"y" + v} x={m.l - 8} y={sy(v) + 4} fontSize="11" fill="var(--muted)" textAnchor="end">{k(v)}</text>)}
      {xt.map((v) => <text key={"x" + v} x={sx(v)} y={H - m.b + 16} fontSize="11" fill="var(--muted)" textAnchor="middle">{k(v)}</text>)}
      <text x={(m.l + W - m.r) / 2} y={H - 6} fontSize="11" fill="var(--ink-2)" textAnchor="middle">exposure, meals (not illnesses)</text>
      <text transform={`translate(14 ${(m.t + H - m.b) / 2}) rotate(-90)`} fontSize="11" fill="var(--ink-2)" textAnchor="middle">avoidable loss, meals</text>
      <path d={path} fill="none" stroke="var(--c1)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      {points.map((p, i) => (
        <g key={i} onClick={() => onSelect(i)} style={{ cursor: "pointer" }}>
          <circle cx={sx(p.exposure_meals)} cy={sy(p.avoidable_loss_meals)} r={i === selectedIndex ? 7 : 4.5}
            fill={i === selectedIndex ? "var(--c2)" : "var(--c1)"} stroke="var(--surface)" strokeWidth="2" />
          <title>{`hold at ${p.hold_at} · recall ${p.recall} · loss ${p.avoidable_loss_meals.toLocaleString()} meals · exposure ${p.exposure_meals.toLocaleString()} meals`}</title>
        </g>
      ))}
      {selectedIndex != null && (
        <text x={sx(points[selectedIndex].exposure_meals) + 10} y={sy(points[selectedIndex].avoidable_loss_meals) - 8} fontSize="11" fill="var(--ink)">hold at {points[selectedIndex].hold_at}</text>
      )}
    </svg>
  );
}
